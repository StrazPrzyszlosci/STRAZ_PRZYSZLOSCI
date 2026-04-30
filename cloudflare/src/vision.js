import { buildPromptPayload, extractJsonObject, formatDeviceName, toIsoNow } from "./base_utils.js";
import { sendTelegramReply } from "./telegram_utils.js";
import { callProviderWithFallback } from "./ai_providers.js";
import { fetchTelegramFileAsBase64 } from "./history.js";
import { getDeviceById, recordRecycledSubmission, getPartsForModel } from "./recycled_catalog.js";
import { upsertUserSession } from "./sessions.js";
import { buildVisionAntiInjectionPrefix } from "./input_sanitizer.js";

export async function recognizeDeviceAndListParts(env, message, mediaBase64) {
  const mediaData = [{ data: mediaBase64, mime_type: message.mime_type || "image/jpeg" }];
  const visionSystem = [
    "Jesteś ekspertem elektroniki i recyklingu.",
    "Na zdjęciu może znajdować się etykieta urządzenia, chip LUB rezystor.",
    "Jeśli to rezystor (THT/SMD), odczytaj jego wartość i zwróć JSON: { \"type\": \"resistor\", \"value\": \"... Ω\", \"value_ohm\": liczba, \"tolerance\": \"...%\", \"bands\": [\"kolor1\", ...], \"smd_code\": \"kod SMD\", \"code_format\": \"THT\" lub \"SMD\", \"confidence\": 0.9 }",
    "Dla THT wypisz kolory pasków po kolei (czarny, brązowy, czerwony, pomarańczowy, żółty, zielony, niebieski, fioletowy, szary, biały, złoty, srebrny).",
    "Jeśli to urządzenie/chip, zidentyfikuj model i zwróć: { \"type\": \"device\", \"brand\": \"...\", \"model\": \"...\", \"confidence\": 0.9 }",
    "Jeśli nie rozpoznajesz obiektu, zwróć: { \"type\": \"unknown\", \"confidence\": 0.0 }",
    "BEZWZGLĘDNIE POMIJAJ numery IMEI - to dane wrażliwe.",
    "Zwróć TYLKO wynik w formacie JSON bez Markdownu.",
    buildVisionAntiInjectionPrefix(),
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
  let calcResult = null;
  let aiOhms = identity.value_ohm && typeof identity.value_ohm === "number" ? identity.value_ohm : (identity.value ? parseOhmsFromAI(identity.value) : null);
  if (identity.bands && identity.bands.length >= 3) calcResult = calculateTHTFromBands(identity.bands);
  else if (identity.smd_code) calcResult = calculateSMDFromCode(identity.smd_code);
  const verText = buildVerificationReply(identity, calcResult, aiOhms);
  const editData = identity.bands && identity.bands.length >= 3
    ? `THT:${identity.bands.join(",")}`
    : identity.smd_code
    ? `SMD:${identity.smd_code}`
    : null;
  const kb = [];
  if (editData) kb.push([{ text: "🔍 Weryfikuj", callback_data: "resistor_edit_bands" }]);
  kb.push([{ text: "📖 Legenda kolorów", callback_data: "resistor_legend" }]);
  kb.push([{ text: "🏠 Menu główne", callback_data: "command_start" }]);
  return {
    reply_text: verText, reply_markup: { inline_keyboard: kb }, _resistor_edit_data: editData,
    _ai_resistor: { value: identity.value, tolerance: identity.tolerance, code_format: identity.code_format, value_ohm: aiOhms },
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
    "Jeśli część całkowicie nie nadaje się do identyfikacji, zwróć { \"error\": \"not_recognized\" }.",
    buildVisionAntiInjectionPrefix(),
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

const THT_COLOR_MAP = {
  czarny:    { digit: 0, multiplier: 1,           tolerance: null },
  brązowy:   { digit: 1, multiplier: 10,          tolerance: "1%" },
  czerwony:  { digit: 2, multiplier: 100,         tolerance: "2%" },
  pomarańczowy: { digit: 3, multiplier: 1e3,      tolerance: null },
  żółty:     { digit: 4, multiplier: 1e4,         tolerance: null },
  zielony:   { digit: 5, multiplier: 1e5,         tolerance: "0.5%" },
  niebieski: { digit: 6, multiplier: 1e6,         tolerance: "0.25%" },
  fioletowy: { digit: 7, multiplier: 1e7,         tolerance: "0.1%" },
  szary:     { digit: 8, multiplier: 1e8,         tolerance: "0.05%" },
  biały:     { digit: 9, multiplier: 1e9,         tolerance: null },
  złoty:     { digit: null, multiplier: 0.1,      tolerance: "5%" },
  srebrny:   { digit: null, multiplier: 0.01,     tolerance: "10%" },
};

const THT_COLOR_ALIASES = {
  black: "czarny", brown: "brązowy", red: "czerwony", orange: "pomarańczowy",
  yellow: "żółty", green: "zielony", blue: "niebieski", violet: "fioletowy",
  purple: "fioletowy", grey: "szary", gray: "szary", white: "biały",
  gold: "złoty", silver: "srebrny",
  brąz: "brązowy", czer: "czerwony", pom: "pomarańczowy", żółt: "żółty",
  ziel: "zielony", nieb: "niebieski", fio: "fioletowy", srebr: "srebrny",
};

function normalizeColorName(raw) {
  const key = String(raw || "").trim().toLowerCase()
    .replace(/[ąа]/g, "a").replace(/[ćс]/g, "c").replace(/[ęe]/g, "e")
    .replace(/[łl]/g, "l").replace(/[ńn]/g, "n").replace(/[óo]/g, "o")
    .replace(/[śs]/g, "s").replace(/[źz]/g, "z").replace(/[żz]/g, "z");
  if (THT_COLOR_ALIASES[key]) return THT_COLOR_ALIASES[key];
  for (const [alias, canonical] of Object.entries(THT_COLOR_ALIASES)) {
    if (key.startsWith(alias) || alias.startsWith(key)) return canonical;
  }
  for (const canonical of Object.keys(THT_COLOR_MAP)) {
    const norm = canonical.toLowerCase()
      .replace(/[ąа]/g, "a").replace(/[ćс]/g, "c").replace(/[ęe]/g, "e")
      .replace(/[łl]/g, "l").replace(/[ńn]/g, "n").replace(/[óo]/g, "o")
      .replace(/[śs]/g, "s").replace(/[źz]/g, "z").replace(/[żz]/g, "z");
    if (norm === key || key.startsWith(norm) || norm.startsWith(key)) return canonical;
  }
  return raw;
}

function calculateTHTFromBands(bands) {
  if (!Array.isArray(bands) || bands.length < 3) return null;
  const resolved = bands.map(b => normalizeColorName(b));
  for (const c of resolved) {
    if (!THT_COLOR_MAP[c]) return null;
  }

  const bandCount = resolved.length;
  let ohms, tolerance;

  if (bandCount === 4) {
    const d1 = THT_COLOR_MAP[resolved[0]].digit;
    const d2 = THT_COLOR_MAP[resolved[1]].digit;
    const mult = THT_COLOR_MAP[resolved[2]].multiplier;
    tolerance = THT_COLOR_MAP[resolved[3]].tolerance;
    if (d1 === null || d2 === null || mult === null) return null;
    ohms = (d1 * 10 + d2) * mult;
  } else if (bandCount === 5) {
    const d1 = THT_COLOR_MAP[resolved[0]].digit;
    const d2 = THT_COLOR_MAP[resolved[1]].digit;
    const d3 = THT_COLOR_MAP[resolved[2]].digit;
    const mult = THT_COLOR_MAP[resolved[3]].multiplier;
    tolerance = THT_COLOR_MAP[resolved[4]].tolerance;
    if (d1 === null || d2 === null || d3 === null || mult === null) return null;
    ohms = (d1 * 100 + d2 * 10 + d3) * mult;
  } else if (bandCount === 6) {
    const d1 = THT_COLOR_MAP[resolved[0]].digit;
    const d2 = THT_COLOR_MAP[resolved[1]].digit;
    const d3 = THT_COLOR_MAP[resolved[2]].digit;
    const mult = THT_COLOR_MAP[resolved[3]].multiplier;
    tolerance = THT_COLOR_MAP[resolved[4]].tolerance;
    if (d1 === null || d2 === null || d3 === null || mult === null) return null;
    ohms = (d1 * 100 + d2 * 10 + d3) * mult;
  } else {
    return null;
  }

  return { ohms, tolerance: tolerance || null, bands: resolved, bandCount };
}

function calculateSMDFromCode(code) {
  const c = String(code || "").trim();
  if (!/^\d{3,4}[A-Z]?$/.test(c) && !/^\d+R\d*$/i.test(c) && !/^\d+\.\d+R$/i.test(c)) return null;

  if (/^\d+R\d*$/i.test(c) || /^\d+\.\d+R$/i.test(c)) {
    const ohms = parseFloat(c.replace(/R/i, "."));
    return { ohms, tolerance: null, smdCode: c };
  }

  const match = c.match(/^(\d{3,4})([A-Z])?$/);
  if (!match) return null;
  const digits = match[1];
  const suffix = match[2] || null;

  if (suffix === "R") {
    return { ohms: parseFloat(digits.slice(0, -1) + "." + digits.slice(-1)), tolerance: null, smdCode: c };
  }

  const n = digits.length;
  const significand = parseInt(digits.slice(0, n - 1), 10);
  const exponent = parseInt(digits.slice(n - 1), 10);
  const ohms = significand * Math.pow(10, exponent);
  return { ohms, tolerance: null, smdCode: c };
}

function formatOhms(ohms) {
  if (ohms === null || ohms === undefined) return null;
  if (ohms >= 1e6 && ohms % 1e6 === 0) return `${ohms / 1e6} MΩ`;
  if (ohms >= 1e3 && ohms % 1e3 === 0) return `${ohms / 1e3} kΩ`;
  if (ohms >= 1e3) return `${(ohms / 1e3).toFixed(2)} kΩ`;
  if (ohms < 1 && ohms > 0) return `${ohms} Ω`;
  return `${ohms} Ω`;
}

function parseOhmsFromAI(valueStr) {
  if (!valueStr) return null;
  const s = String(valueStr).replace(/[ΩOhm\s]/gi, "").replace(",", ".").trim();
  const m = s.match(/^([\d.]+)\s*([kKMmGg])?$/);
  if (!m) return null;
  let val = parseFloat(m[1]);
  if (isNaN(val)) return null;
  const prefix = (m[2] || "").toLowerCase();
  if (prefix === "k") val *= 1e3;
  else if (prefix === "m") val *= 1e6;
  else if (prefix === "g") val *= 1e9;
  return val;
}

function compareValues(aiOhms, calcOhms) {
  if (aiOhms === null || calcOhms === null) return "inconclusive";
  if (aiOhms === calcOhms) return "match";
  const ratio = Math.max(aiOhms, calcOhms) / Math.min(aiOhms, calcOhms);
  if (ratio <= 1.001) return "match";
  if (ratio <= 10) return "mismatch_minor";
  return "mismatch_major";
}

function buildVerificationReply(aiResult, calcResult, aiOhms) {
  const aiFormatted = aiResult.value || "—";
  const aiTolerance = aiResult.tolerance || "—";
  const codeFormat = aiResult.code_format || "—";
  const aiBands = aiResult.bands && aiResult.bands.length > 0 ? aiResult.bands.join(" → ") : "—";
  const aiConfidence = aiResult.confidence ? Math.round(aiResult.confidence * 100) : null;

  let lines = [];
  lines.push(`🎨 *Wynik odczytu rezystora:*`);
  lines.push("");
  lines.push(`📊 Wartość AI: *${aiFormatted}*`);
  if (aiTolerance !== "—") lines.push(`📏 Tolerancja AI: ${aiTolerance}`);
  if (codeFormat !== "—") lines.push(`🔧 Format: ${codeFormat}`);
  if (aiBands !== "—") lines.push(`🎨 Paski AI: ${aiBands}`);
  if (aiConfidence !== null) lines.push(`🤖 Pewność AI: ${aiConfidence}%`);
  lines.push("");
  lines.push("_Kliknij 🔍 Weryfikuj poniżej, aby przeliczyć rozpoznane kolory/kod niezależnym algorytmem i porównać z wynikiem AI._");

  return lines.join("\n");
}

export function buildVerificationResultReply(aiResult, calcResult, aiOhms) {
  if (!calcResult) return "❌ Nie udało się przeliczyć podanych danych algorytmem. Sprawdź poprawność kolorów/kodu.";
  const aiFormatted = aiResult.value || "—";
  const calcFormatted = formatOhms(calcResult.ohms);
  const calcTolerance = calcResult.tolerance || "—";
  const verification = compareValues(aiOhms, calcResult.ohms);
  let lines = [];
  lines.push("🔍 *Weryfikacja algorytmiczna:*");
  lines.push("");
  lines.push(`📊 Wartość AI: *${aiFormatted}*`);
  if (calcResult.bands) {
    lines.push(`📐 Obliczono z pasków (${calcResult.bandCount}-paskowy): *${calcFormatted}*`);
    lines.push(`🎨 Paski: ${calcResult.bands.join(" → ")}`);
  } else if (calcResult.smdCode) {
    lines.push(`📐 Obliczono z kodu SMD \`${calcResult.smdCode}\`: *${calcFormatted}*`);
  }
  if (calcTolerance !== "—") lines.push(`📏 Tolerancja: ${calcTolerance}`);
  lines.push("");
  if (verification === "match") {
    lines.push("✅ *Wynik zweryfikowany* — obliczenia algorytmiczne potwierdzają odpowiedź modelu AI. Odczyt jest spójny i wiarygodny.");
  } else if (verification === "mismatch_minor") {
    lines.push("⚠️ *Niewielka rozbieżność* — wartość AI i obliczona różnią się, ale w granicach jednego rzędu wielkości. Możliwy błąd w rozpoznaniu paska mnożnika. Zalecam ostrożność.");
    lines.push(`🔍 AI: ${aiFormatted} | Obliczono: ${calcFormatted}`);
  } else if (verification === "mismatch_major") {
    lines.push("🚨 *Istotna rozbieżność* — odpowiedź AI znacząco odstaje od obliczeń algorytmicznych. Prawdopodobne halucynacje modelu. Zdecydowanie polecam weryfikację ręczną.");
    lines.push(`🔍 AI: ${aiFormatted} | Obliczono: *${calcFormatted}*`);
  } else {
    lines.push("❓ *Weryfikacja niejednoznaczna* — nie udało się porównać wyników.");
  }
  lines.push("");
  lines.push("_Warstwa zabezpieczająca: oznaczenia przeliczono niezależnym algorytmem i skonfrontowano z odpowiedzią AI._");
  return lines.join("\n");
}

export async function handleResistorAnalysis(env, message) {
  if (!message.file_id) return { reply_text: "Aby odczytać rezystor, wyślij jego zdjęcie." };
  await sendTelegramReply(env, message, "🎨 Analizuję paski/kod na rezystorze...");
  const base64 = await fetchTelegramFileAsBase64(env, message.file_id);
  if (!base64) return { reply_text: "❌ Nie udało się pobrać zdjęcia z Telegrama. Spróbuj przesłać je ponownie." };

  const resistorSystem = [
    "Jesteś ekspertem elektroniki specjalizującym się w odczycie rezystorów.",
    "Na zdjęciu znajduje się rezystor. Odczytaj jego wartość na podstawie pasków kolorów (THT) lub kodu alfanumerycznego (SMD).",
    "",
    "Zwróć TYLKO JSON w formacie:",
    "{",
    "  \"type\": \"resistor\",",
    "  \"value\": \"wartość w Ohm (np. 4.7 kΩ, 220 Ω, 1 MΩ)\",",
    "  \"value_ohm\": liczba_w_ohmach,",
    "  \"tolerance\": \"np. 5% lub 1%\",",
    "  \"bands\": [\"kolor1\", \"kolor2\", ...],",
    "  \"smd_code\": \"kod SMD jeśli applicable, np. 103, 47R\",",
    "  \"code_format\": \"THT\" lub \"SMD\",",
    "  \"confidence\": 0.9",
    "}",
    "",
    "Dla THT: wypisz kolory WSZYSTKICH pasków po kolei (od lewej do prawej), używając polskich nazw:",
    "czarny, brązowy, czerwony, pomarańczowy, żółty, zielony, niebieski, fioletowy, szary, biały, złoty, srebrny.",
    "Dla SMD: wypisz dokładny kod z obudowy w polu smd_code.",
    "",
    "Pole value_ohm musi być liczbą (np. 4700, nie \"4.7k\").",
    "Jeśli nie jesteś w stanie odczytać wartości, zwróć: { \"type\": \"resistor\", \"error\": \"nie_udało_sie_odczytać\", \"reason\": \"opis powodu\" }",
    "Zwróć TYLKO JSON bez Markdown."
  ].join("\n");

  try {
    const visionResp = await callProviderWithFallback(env, buildPromptPayload(resistorSystem, "Odczytaj wartość tego rezystora ze zdjęcia. Wypisz dokładne kolory pasków lub kod SMD.", env, {
      media: [{ data: base64, mime_type: message.mime_type || "image/jpeg" }],
      responseMimeType: "application/json", maxTokens: 600
    }));

    const identity = extractJsonObject(visionResp.text);

    if (identity.error) {
      return {
        reply_text: `🎨 *Odczyt rezystora:*\nNie udało się jednoznacznie odczytać wartości.\n_powód: ${identity.reason || "niewyraźne zdjęcie"}_\n\nSpróbuj przesłać wyraźniejsze zdjęcie z bliska.`,
        provider_name: visionResp.provider_name, model_name: visionResp.model_name
      };
    }

    let calcResult = null;
    let aiOhms = null;

    if (identity.value_ohm && typeof identity.value_ohm === "number") {
      aiOhms = identity.value_ohm;
    } else if (identity.value) {
      aiOhms = parseOhmsFromAI(identity.value);
    }

    if (identity.code_format === "THT" && identity.bands && identity.bands.length >= 3) {
      calcResult = calculateTHTFromBands(identity.bands);
    } else if (identity.code_format === "SMD" && identity.smd_code) {
      calcResult = calculateSMDFromCode(identity.smd_code);
    } else if (identity.bands && identity.bands.length >= 3) {
      calcResult = calculateTHTFromBands(identity.bands);
    } else if (identity.smd_code) {
      calcResult = calculateSMDFromCode(identity.smd_code);
    }

  const replyText = buildVerificationReply(identity, calcResult, aiOhms);
  const editData = identity.bands && identity.bands.length >= 3
    ? `THT:${identity.bands.join(",")}`
    : identity.smd_code
    ? `SMD:${identity.smd_code}`
    : null;
  const kb = [];
  if (editData) kb.push([{ text: "🔍 Weryfikuj", callback_data: "resistor_edit_bands" }]);
  kb.push([{ text: "📖 Legenda kolorów", callback_data: "resistor_legend" }]);
  kb.push([{ text: "🏠 Menu główne", callback_data: "command_start" }]);

  return { reply_text: replyText, reply_markup: { inline_keyboard: kb }, _resistor_edit_data: editData, _ai_resistor: { value: identity.value, tolerance: identity.tolerance, code_format: identity.code_format, value_ohm: aiOhms }, provider_name: visionResp.provider_name, model_name: visionResp.model_name };
} catch (error) {
  const errorMsg = error instanceof Error ? error.message : String(error);
  console.error("[handleResistorAnalysis] AI error:", errorMsg);
  return { reply_text: `❌ Wystąpił błąd podczas analizy rezystora: ${errorMsg}. Spróbuj ponownie za chwilę.`, reply_markup: { inline_keyboard: [[{ text: "🏠 Menu główne", callback_data: "command_start" }]] } };
}
}
