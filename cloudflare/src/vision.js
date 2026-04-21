import { buildPromptPayload, extractJsonObject, formatDeviceName, toIsoNow } from "./base_utils.js";
import { sendTelegramReply } from "./telegram_utils.js";
import { callProviderWithFallback } from "./ai_providers.js";
import { fetchTelegramFileAsBase64 } from "./history.js";
import { getDeviceById, recordRecycledSubmission, getPartsForModel } from "./recycled_catalog.js";
import { upsertUserSession } from "./sessions.js";

export async function recognizeDeviceAndListParts(env, message, mediaBase64) {
  const mediaData = [{ data: mediaBase64, mime_type: message.mime_type || "image/jpeg" }];
  const visionSystem = [
    "Jesteś ekspertem elektroniki i recyklingu.",
    "Na zdjęciu może znajdować się etykieta urządzenia, chip LUB rezystor.",
    "Jeśli to rezystor (THT/SMD), odczytaj jego wartość i zwróć JSON: { \"type\": \"resistor\", \"value\": \"... Ohm\", \"tolerance\": \"...%\", \"confidence\": 0.9 }",
    "Jeśli to urządzenie/chip, zidentyfikuj model i zwróć: { \"type\": \"device\", \"brand\": \"...\", \"model\": \"...\", \"confidence\": 0.9 }",
    "Jeśli nie rozpoznajesz obiektu, zwróć: { \"type\": \"unknown\", \"confidence\": 0.0 }",
    "BEZWZGLĘDNIE POMIJAJ numery IMEI - to dane wrażliwe.",
    "Zwróć TYLKO wynik w formacie JSON bez Markdownu."
  ].join(" ");

  let identity;
  let visionResp;
  try {
    visionResp = await callProviderWithFallback(env, buildPromptPayload(visionSystem, "Zidentyfikuj obiekt na zdjęciu (urządzenie lub rezystor).", env, {
      media: mediaData, responseMimeType: "application/json", maxTokens: 300
    }));
    identity = extractJsonObject(visionResp.text);
  } catch (error) {
    const errorMsg = error instanceof Error ? error.message : String(error);
    console.error("[recognizeDeviceAndListParts] AI error:", errorMsg);
    return { reply_text: `❌ Błąd analizy obrazu: ${errorMsg}. Spróbuj ponownie za chwilę lub prześlij wyraźniejsze zdjęcie.` };
  }

  if (identity.type === "resistor") {
    return {
      reply_text: `🔍 Zidentyfikowano rezystor o wartości: *${identity.value}* (pewność: ${Math.round(identity.confidence * 100)}%).`,
      provider_name: visionResp.provider_name, model_name: visionResp.model_name
    };
  }

  if (identity.model) {
    const combinedQuery = [identity.brand, identity.model].filter(Boolean).join(" ");
    const dbResult = (combinedQuery ? await getPartsForModel(env, combinedQuery) : null) || await getPartsForModel(env, identity.model);
    if (dbResult) {
      await recordRecycledSubmission(env, {
        chat_id: message?.chat_id, user_id: message?.user_id, message_id: message?.message_id,
        lookup_kind: "device_media", query_text: combinedQuery || identity.model,
        recognized_brand: identity.brand || null, recognized_model: identity.model || null,
        matched_device_id: dbResult.device.id, attachment_file_id: message?.file_id || null,
        attachment_mime_type: message?.mime_type || null, provider_name: visionResp.provider_name,
        model_name: visionResp.model_name, status: "matched_device", raw_payload_json: identity,
      });

      return {
        reply_text: `Zidentyfikowano: ${formatDeviceName(dbResult.device)}. Czy chcesz teraz dodać zdjęcia konkretnych części z tego egzemplarza?`,
        reply_markup: {
          inline_keyboard: [
            [{ text: "✅ Tak, dodaję części", callback_data: `recycled_add_parts:${dbResult.device.id}` },
             { text: "❌ Nie, tylko info", callback_data: `recycled_show_info:${dbResult.device.id}` }]
          ]
        },
        provider_name: visionResp.provider_name, model_name: visionResp.model_name
      };
    }

    await recordRecycledSubmission(env, {
      chat_id: message?.chat_id, user_id: message?.user_id, message_id: message?.message_id,
      lookup_kind: "device_media", query_text: combinedQuery || identity.model,
      recognized_brand: identity.brand || null, recognized_model: identity.model || null,
      attachment_file_id: message?.file_id || null, attachment_mime_type: message?.mime_type || null,
      provider_name: visionResp.provider_name, model_name: visionResp.model_name,
      status: "queued", raw_payload_json: identity,
    });

    return {
      reply_text: `Zidentyfikowano urządzenie: ${formatDeviceName(identity)}. Nie mam go jeszcze w katalogu reuse, ale zgłoszenie trafiło do kolejki kuracji. Czy mimo to chcesz przesłać zdjęcia jego części dla dokumentacji?`,
      reply_markup: {
        inline_keyboard: [
          [{ text: "✅ Tak, prześlij części", callback_data: `recycled_add_parts_unknown:${formatDeviceName(identity).substring(0, 30)}` },
           { text: "❌ Nie", callback_data: "recycled_cancel" }]
        ]
      },
      provider_name: visionResp.provider_name, model_name: visionResp.model_name
    };
  }

  await recordRecycledSubmission(env, {
    chat_id: message?.chat_id, user_id: message?.user_id, message_id: message?.message_id,
    lookup_kind: "device_media", attachment_file_id: message?.file_id || null,
    attachment_mime_type: message?.mime_type || null, provider_name: visionResp.provider_name,
    model_name: visionResp.model_name, status: "unrecognized", raw_payload_json: identity,
  });
  
  return {
    reply_text: "Nie udało mi się jednoznacznie zidentyfikować modelu na zdjęciu. Spróbuj przesłać wyraźniejsze zdjęcie naklejki znamionowej.",
    provider_name: visionResp.provider_name, model_name: visionResp.model_name
  };
}

export async function recognizePartAndRecord(env, message, mediaBase64, session, ctx = null) {
  const mediaData = [{ data: mediaBase64, mime_type: message.mime_type || "image/jpeg" }];
  const visionSystem = [
    "Jesteś ekspertem od elektroniki i części zamiennych.",
    "Zidentyfikuj część ze zdjęcia (odczytaj numery z etykiety, układów scalonych, chipu PCB itp.).",
    "BEZWZGLĘDNIE POMIJAJ numery IMEI.",
    "Zwróć wynik TYLKO w formacie JSON podając typ i numery, bez Markdownu z kodem. Oczekiwany format: { \"part_name\": \"krótka nazwa np. Płyta główna, Pamięć RAM, Bateria\", \"part_number\": \"zidentyfikowane oznaczenia\", \"confidence\": 0.9 }",
    "Jeśli część całkowicie nie nadaje się do identyfikacji, zwróć { \"error\": \"not_recognized\" }."
  ].join(" ");
  
  const visionResp = await callProviderWithFallback(env, buildPromptPayload(visionSystem, "Zidentyfikuj tę część i odczytaj wszystkie przydatne numery serwisowe/part numbers z widocznych naklejek.", env, {
    media: mediaData, responseMimeType: "application/json", maxTokens: 400
  }));
  
  const identity = extractJsonObject(visionResp.text);
  const partName = identity.part_name || (identity.error ? "Nierozpoznana część" : "Część urządzenia");
  let partNumber = identity.part_number || "Brak wyraźnych oznaczeń";
  if (typeof partNumber === "string") {
    partNumber = partNumber.replace(/\b\d{15}\b/g, "[REDACTED IMEI]");
  }

  let deviceName = session.active_device_name;
  if (!deviceName && session.active_device_id) {
    const device = await getDeviceById(env, session.active_device_id);
    if (device) deviceName = `${device.brand || ""} ${device.model || ""}`.trim();
  }

  const submissionId = await recordRecycledSubmission(env, {
    chat_id: message?.chat_id, user_id: message?.user_id, message_id: message?.message_id,
    lookup_kind: "part_media", matched_device_id: session.active_device_id,
    query_text: deviceName || null, matched_part_name: identity.part_name || null,
    matched_part_number: identity.part_number || null, attachment_file_id: message?.file_id || null,
    attachment_mime_type: message?.mime_type || null, provider_name: visionResp.provider_name,
    model_name: visionResp.model_name, status: "queued", raw_payload_json: identity,
  });
  
  let replyText = `✅ Zidentyfikowano część: *${partName}*`;
  if (partNumber && partNumber !== "Brak wyraźnych oznaczeń") {
    replyText += `\n🔢 Oznaczenia odczytane przez AI: \`${partNumber}\``;
  }
  replyText += `\n\nCzy zgadza się to z rzeczywistością? Uruchomiłem tryb edycji. Możesz teraz podać poprawną nazwę i numer części w formacie: \`Nazwa | Numer\`, albo po prostu zatwierdzić przyciskiem poniżej.`;

  await upsertUserSession(env, message?.chat_id, message?.user_id, "recycled_parts_edit", session.active_device_id || null, `submission:${submissionId}`);

  return {
    reply_text: replyText,
    reply_markup: {
      inline_keyboard: [
        [{ text: "✅ Dodaj do bazy", callback_data: `recycled_part_add:${submissionId}` },
         { text: "✏️ Edytuj dane części", callback_data: `recycled_part_edit:${submissionId}` }],
        [{ text: "📄 Datasheet & AI", callback_data: `datasheet_start_search:${partNumber || partName}` }]
      ]
    },
    provider_name: visionResp.provider_name, model_name: visionResp.model_name
  };
}

export async function handleResistorAnalysis(env, message) {
  if (!message.file_id) return { reply_text: "Aby odczytać rezystor, wyślij jego zdjęcie." };
  await sendTelegramReply(env, message, "🎨 Analizuję paski/kod na rezystorze...");
  const base64 = await fetchTelegramFileAsBase64(env, message.file_id);
  if (!base64) return { reply_text: "❌ Nie udało się pobrać zdjęcia z Telegrama. Spróbuj przesłać je ponownie." };

  const resistorSystem = [
    "Jesteś ekspertem elektroniki specjalizującym się w odczycie rezystorów.",
    "Na zdjęciu znajduje się rezystor. Odczytaj jego wartość na podstawie pasków kolorów (THT) lub kodu alfanumerycznego (SMD).",
    "Zwróć TYLKO JSON w formacie: { \"type\": \"resistor\", \"value\": \"... Ohm\", \"tolerance\": \"...%\", \"bands\": [\"kolor1\", \"kolor2\", ...], \"code_format\": \"THT\" lub \"SMD\", \"confidence\": 0.9 }",
    "Jeśli nie jesteś w stanie odczytać wartości, zwróć: { \"type\": \"resistor\", \"error\": \"nie_udało_sie_odczytać\", \"reason\": \"opis powodu\" }",
    "Zwróć TYLKO JSON bez Markdown."
  ].join(" ");

  try {
    const visionResp = await callProviderWithFallback(env, buildPromptPayload(resistorSystem, "Odczytaj wartość tego rezystora ze zdjęcia.", env, {
      media: [{ data: base64, mime_type: message.mime_type || "image/jpeg" }], responseMimeType: "application/json", maxTokens: 400
    }));

    const identity = extractJsonObject(visionResp.text);

    if (identity.error) {
      return {
        reply_text: `🎨 *Odczyt rezystora:*\nNie udało się jednoznacznie odczytać wartości.\n_powód: ${identity.reason || "niewyraźne zdjęcie"}_\n\nSpróbuj przesłać wyraźniejsze zdjęcie z bliska.`,
        provider_name: visionResp.provider_name, model_name: visionResp.model_name
      };
    }

    let replyText = `🎨 *Wynik odczytu rezystora:*\n\n📊 Wartość: *${identity.value}*`;
    if (identity.tolerance) replyText += `\n📏 Tolerancja: ${identity.tolerance}`;
    if (identity.code_format) replyText += `\n🔧 Format: ${identity.code_format}`;
    if (identity.bands && identity.bands.length > 0) replyText += `\n🎨 Paski: ${identity.bands.join(" → ")}`;
    if (identity.confidence) replyText += `\n✅ Pewność: ${Math.round(identity.confidence * 100)}%`;

    return { reply_text: replyText, provider_name: visionResp.provider_name, model_name: visionResp.model_name };
  } catch (error) {
    const errorMsg = error instanceof Error ? error.message : String(error);
    console.error("[handleResistorAnalysis] AI error:", errorMsg);
    return { reply_text: `❌ Wystąpił błąd podczas analizy rezystora: ${errorMsg}. Spróbuj ponownie za chwilę.` };
  }
}
