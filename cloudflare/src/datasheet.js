import { fetchTelegramFileAsBase64 } from "./history.js";
import { sendTelegramReply } from "./telegram_utils.js";
import { upsertUserSession, closeUserSession } from "./sessions.js";
import { recordRecycledSubmission } from "./recycled_catalog.js";
import { callProviderWithFallback } from "./ai_providers.js";
import { buildPromptPayload } from "./base_utils.js";

const PDF_SEARCH_SOURCES = [
  { name: "LCSC", url: "https://www.lcsc.com/search?keyword=", parse: "lcsc" },
  { name: "DigiKey", url: "https://www.digikey.com/en/search?q=", parse: "digikey" },
  { name: "Mouser", url: "https://www.mouser.com/Search?q=", parse: "mouser" },
  { name: "SparkFun", url: "https://www.sparkfun.com/search/results?term=", parse: "sparkfun" },
];

async function searchDatasheetUrl(partName) {
  const normalizedPart = partName.trim().replace(/\s+/g, "+");
  for (const source of PDF_SEARCH_SOURCES) {
    try {
      const searchUrl = source.url + encodeURIComponent(normalizedPart);
      const resp = await fetch(searchUrl, {
        headers: { "User-Agent": "Mozilla/5.0 (compatible; StrażPrzyszłościBot/1.0)" },
        redirect: "follow",
      });
      if (resp.ok) {
        const text = await resp.text();
        const pdfLink = extractPdfLink(text, source.parse, resp.url);
        if (pdfLink) {
          return { url: pdfLink, source: source.name };
        }
      }
    } catch {
      // continue to next source
    }
  }
  return null;
}

function extractPdfLink(html, sourceType, baseUrl) {
  if (!html) return null;

  const patterns = [
    /href="([^"]*\.pdf[^"]*)"/i,
    /data-datasheet="([^"]*\.pdf[^"]*)"/i,
    /src="([^"]*datasheet[^"]*\.pdf[^"]*)"/i,
    /a[^>]+href="([^"]*product[^"]*\.pdf[^"]*)"/i,
  ];

  for (const pattern of patterns) {
    const match = html.match(pattern);
    if (match && match[1]) {
      let url = match[1];
      if (url.startsWith("//")) url = "https:" + url;
      else if (url.startsWith("/")) {
        try {
          const base = new URL(baseUrl);
          url = base.origin + url;
        } catch {
          continue;
        }
      } else if (!url.startsWith("http")) {
        continue;
      }
      if (url.includes(".pdf") || url.includes("datasheet")) {
        return url;
      }
    }
  }

  if (sourceType === "lcsc") {
    const lcscMatch = html.match(/"datasheetUrl"\s*:\s*"([^"]+)"/);
    if (lcscMatch?.[1]) return lcscMatch[1];
  }

  return null;
}

async function downloadPdfAsBase64(pdfUrl) {
  try {
    const resp = await fetch(pdfUrl, {
      headers: { "User-Agent": "Mozilla/5.0 (compatible; StrażPrzyszłościBot/1.0)" },
    });
    if (!resp.ok || !resp.headers.get("content-type")?.includes("pdf")) {
      return null;
    }
    const buffer = await resp.arrayBuffer();
    const uint8 = new Uint8Array(buffer);
    let binary = "";
    const chunkSize = 8192;
    for (let i = 0; i < uint8.length; i += chunkSize) {
      const chunk = uint8.subarray(i, Math.min(i + chunkSize, uint8.length));
      binary += String.fromCharCode.apply(null, chunk);
    }
    return btoa(binary);
  } catch {
    return null;
  }
}

async function findAndDownloadDatasheetPdf(partName) {
  const searchResult = await searchDatasheetUrl(partName);
  if (!searchResult) return { url: null, base64: null, source: null };

  const base64 = await downloadPdfAsBase64(searchResult.url);
  return {
    url: searchResult.url,
    base64,
    source: searchResult.source,
  };
}

export async function initDatasheetWorkflow(env, message, intent) {
  const query = (message.text || message.caption || "Analiza dokumentu PDF").trim();
  const fileId = message.file_id || null;

  if (fileId && message.mime_type === "application/pdf") {
    await upsertUserSession(env, message.chat_id, message.user_id, "datasheet_wait_model", fileId, `PDF|${query}`);
    return {
      reply_text: `📄 *Otrzymałem PDF:*\n\`${query}\`\n\nTeraz podaj nazwę modelu/układu (np. \`NE555\`, \`ESP8266\`) lub wyślij zdjęcie etykiety urządzenia, abym wiedział, czego dotyczy ten datasheet.`,
      reply_markup: {
        inline_keyboard: [[{ text: "❌ Anuluj", callback_data: "cancel_session:datasheet_wait_model" }]]
      }
    };
  }

  await sendTelegramReply(env, message, `🔍 Szukam datasheet dla: *${query}*...`);
  const searchResult = await findAndDownloadDatasheetPdf(query);

  if (searchResult.base64) {
    await upsertUserSession(env, message.chat_id, message.user_id, "datasheet_wait_model", "pdf_downloaded", `${query}|${searchResult.url}|${searchResult.source}`);
    return {
      reply_text: `✅ *Znaleziono datasheet!*\n\n📄 *${query}*\n🔗 Źródło: ${searchResult.source}\n🌐 ${searchResult.url}\n\nPrzeanalizuję go po podaniu pytania. O co chcesz zapytać?`,
      reply_markup: {
        inline_keyboard: [
          [{ text: "🌐 Otwórz PDF", url: searchResult.url }],
          [{ text: "💬 Zadaj pytanie", callback_data: `datasheet_ask:${query}` }],
          [{ text: "❌ Anuluj", callback_data: "cancel_session:datasheet_wait_model" }]
        ]
      }
    };
  }

  if (searchResult.url) {
    await upsertUserSession(env, message.chat_id, message.user_id, "datasheet_wait_model", null, `${query}|${searchResult.url}|${searchResult.source}`);
    return {
      reply_text: `🔗 *Znaleziono stronę producenta*\n\n📄 *${query}*\n🔗 Źródło: ${searchResult.source}\n🌐 ${searchResult.url}\n\nMogę spróbować przeanalizować stronę, ale zalecam pobrać PDF i przesłać go bezpośrednio. Co wolisz zrobić?`,
      reply_markup: {
        inline_keyboard: [
          [{ text: "🌐 Otwórz stronę", url: searchResult.url }],
          [{ text: "📤 Pobierz PDF i wyślij mi", callback_data: `datasheet_download_pdf:${searchResult.url}` }],
          [{ text: "❌ Anuluj", callback_data: "cancel_session:datasheet_wait_model" }]
        ]
      }
    };
  }

  await upsertUserSession(env, message.chat_id, message.user_id, "datasheet_wait_model", fileId, query);
  return {
    reply_text: `📄 *Asystent Dokumentacji Aktywny!*\n\nSzukam: *${query}*\n\nNie znalazłem automatycznie datasheet. Możesz:\n• Wpisać nazwę modelu (np. \`NE555\`, \`LM7805\`)\n• Przesłać zdjęcie etykiety urządzenia\n• Przesłać plik PDF z dokumentacją`,
    reply_markup: {
      inline_keyboard: [[{ text: "❌ Anuluj", callback_data: "cancel_session:datasheet_wait_model" }]]
    }
  };
}

export async function handleDatasheetDownloadPdf(env, message, pdfUrl) {
  await sendTelegramReply(env, message, `📥 Pobieram PDF z: ${pdfUrl}...`);
  const base64 = await downloadPdfAsBase64(pdfUrl);

  if (base64) {
    const searchResult = await findAndDownloadDatasheetPdf(pdfUrl);
    await upsertUserSession(env, message.chat_id, message.user_id, "datasheet_wait_model", "pdf_downloaded", `PDF z URL|${pdfUrl}|Pobrane`);
    return {
      reply_text: `✅ *PDF pobrany poprawnie!*\n\nTeraz wpisz pytanie na temat tego układu, a przeanalizuję dokumentację.`,
      reply_markup: {
        inline_keyboard: [
          [{ text: "🌐 Otwórz PDF", url: pdfUrl }],
          [{ text: "❌ Anuluj", callback_data: "cancel_session:datasheet_wait_model" }]
        ]
      }
    };
  }

  return {
    reply_text: `❌ Nie udało się pobrać PDF. Spróbuj ręcznie pobrać plik i przesłać go bezpośrednio do bota.`,
    reply_markup: {
      inline_keyboard: [
        [{ text: "🌐 Otwórz stronę", url: pdfUrl }],
        [{ text: "❌ Anuluj", callback_data: "cancel_session:datasheet_wait_model" }]
      ]
    }
  };
}

export async function handleFinalDatasheetRag(env, message, session, deviceModel, ctx = null) {
  await sendTelegramReply(env, message, `⏳ Przyjąłem model: *${deviceModel}*.`);

  const sessionData = session.active_device_name.split("|");
  const partQuery = sessionData[0] || "Nieznana część";
  const pdfUrl = sessionData[1] || null;
  const pdfSource = sessionData[2] || null;

  if (pdfUrl === "pdf_downloaded") {
    await upsertUserSession(env, message.chat_id, message.user_id, "datasheet_wait_question", session.active_device_id, `${partQuery}|${deviceModel}|PDF|${pdfSource || "Przesłany"}`);
  } else if (pdfUrl && pdfUrl.startsWith("http")) {
    await upsertUserSession(env, message.chat_id, message.user_id, "datasheet_wait_question", null, `${partQuery}|${deviceModel}|URL|${pdfUrl}`);
  } else {
    await upsertUserSession(env, message.chat_id, message.user_id, "datasheet_wait_question", session.active_device_id, `${partQuery}|${deviceModel}`);
  }

  return {
    reply_text: `💡 Część: \`${partQuery}\` | Model: \`${deviceModel}\`\n\nO co chciałbyś zapytać w kontekście tego układu? (np. "Jaki jest pinout?", "Podaj napięcie zasilania", "Zamiennik")`,
    reply_markup: {
      inline_keyboard: pdfUrl && pdfUrl.startsWith("http") ? [[{ text: "🌐 Otwórz PDF/Datasheet", url: pdfUrl }]] : []
    }
  };
}

export async function handleFinalDatasheetRagFinal(env, message, session, userQuestion, ctx = null) {
 const sessionData = session.active_device_name.split("|");
 const partQuery = sessionData[0] || "Nieznana część";
 const deviceModel = sessionData[1] || "Nieznany model";
 const contentType = sessionData[2] || null;
 const sourceInfo = sessionData.slice(3).join("|") || null;

 // ── Anti-Prompt-Injection: sanitize user question ──
 const { sanitizeUserInput, extractAndAnalyzePdf, buildPdfHiddenContentWarning, buildAntiInjectionSystemPrefix, getGenericRejectionMessage, persistAuditToDb } = await import("./input_sanitizer.js");

 const sanitized = sanitizeUserInput(userQuestion || "", {
 chat_id: message?.chat_id,
 user_id: message?.user_id,
 message_id: message?.message_id,
 env,
 });

 if (sanitized.wasBlocked) {
 await closeUserSession(env, message.chat_id, message.user_id, "datasheet_wait_question");
 return {
 reply_text: getGenericRejectionMessage(),
 reply_markup: undefined,
 };
 }

  await sendTelegramReply(env, message, `🔎 Analizuję datasheet pod kątem: _"${sanitized.safeText}"_...`);

 let aiContext = "";
 let finalPdfUrl = null;
 let pdfSecurityWarning = "";

 if (contentType === "PDF" && sourceInfo) {
 const base64 = await fetchTelegramFileAsBase64(env, session.active_device_id);
 if (!base64) {
 const fallback = await findAndDownloadDatasheetPdf(partQuery);
 if (fallback.base64) {
 // ── R3: PDF hidden content analysis ──
 const pdfAnalysis = extractAndAnalyzePdf(fallback.base64);
 pdfSecurityWarning = buildPdfHiddenContentWarning(pdfAnalysis);
 if (pdfAnalysis.isSuspicious) {
 try { await persistAuditToDb(env, { chat_id: message?.chat_id, user_id: message?.user_id, attack_type: "pdf_hidden_content", severity: "high", details: { flags: pdfAnalysis.hiddenContentFlags, warnings: pdfAnalysis.warnings }, action_taken: "flagged_passed" }); } catch { /* non-blocking */ }
 }

 const datasheetSystemPrompt = [
 "Jesteś inżynierem elektronikiem. Analizujesz datasheet PDF. Odpowiedz na pytanie użytkownika na podstawie tego dokumentu. Podaj konkretne informacje z dokumentu.",
 buildAntiInjectionSystemPrefix(),
 pdfSecurityWarning,
 ].join("\n");

 const visionResp = await callProviderWithFallback(env, buildPromptPayload(
 datasheetSystemPrompt,
 `Pytanie: ${sanitized.safeText}\n\nNazwa części: ${partQuery}\nModel: ${deviceModel}`,
 env,
 { media: [{ data: fallback.base64, mime_type: "application/pdf" }], maxTokens: 2000 }
 ));
 aiContext = visionResp.text;
 finalPdfUrl = fallback.url;
 }
 } else {
 // ── R3: PDF hidden content analysis ──
 const pdfAnalysis = extractAndAnalyzePdf(base64);
 pdfSecurityWarning = buildPdfHiddenContentWarning(pdfAnalysis);
 if (pdfAnalysis.isSuspicious) {
 try { await persistAuditToDb(env, { chat_id: message?.chat_id, user_id: message?.user_id, attack_type: "pdf_hidden_content", severity: "high", details: { flags: pdfAnalysis.hiddenContentFlags, warnings: pdfAnalysis.warnings }, action_taken: "flagged_passed" }); } catch { /* non-blocking */ }
 }

 const datasheetSystemPrompt = [
 "Jesteś inżynierem elektronikiem. Analizujesz datasheet PDF. Odpowiedz na pytanie użytkownika na podstawie tego dokumentu. Podaj konkretne informacje z dokumentu.",
 buildAntiInjectionSystemPrefix(),
 pdfSecurityWarning,
 ].join("\n");

 const visionResp = await callProviderWithFallback(env, buildPromptPayload(
 datasheetSystemPrompt,
 `Pytanie: ${sanitized.safeText}\n\nNazwa części: ${partQuery}\nModel: ${deviceModel}`,
 env,
 { media: [{ data: base64, mime_type: "application/pdf" }], maxTokens: 2000 }
 ));
 aiContext = visionResp.text;
 finalPdfUrl = sourceInfo;
 }
 } else if (contentType === "URL" && sourceInfo) {
 const base64 = await downloadPdfAsBase64(sourceInfo);
 if (base64) {
 // ── R3: PDF hidden content analysis ──
 const pdfAnalysis = extractAndAnalyzePdf(base64);
 pdfSecurityWarning = buildPdfHiddenContentWarning(pdfAnalysis);
 if (pdfAnalysis.isSuspicious) {
 try { await persistAuditToDb(env, { chat_id: message?.chat_id, user_id: message?.user_id, attack_type: "pdf_hidden_content", severity: "high", details: { flags: pdfAnalysis.hiddenContentFlags, warnings: pdfAnalysis.warnings }, action_taken: "flagged_passed" }); } catch { /* non-blocking */ }
 }

 const datasheetSystemPrompt = [
 "Jesteś inżynierem elektronikiem. Analizujesz stronę z dokumentacją. Odpowiedz na pytanie użytkownika na podstawie informacji z tej strony.",
 buildAntiInjectionSystemPrefix(),
 pdfSecurityWarning,
 ].join("\n");

 const visionResp = await callProviderWithFallback(env, buildPromptPayload(
 datasheetSystemPrompt,
 `Pytanie: ${sanitized.safeText}\n\nNazwa części: ${partQuery}\nModel: ${deviceModel}`,
 env,
 { media: [{ data: base64, mime_type: "application/pdf" }], maxTokens: 2000 }
 ));
 aiContext = visionResp.text;
 finalPdfUrl = sourceInfo;
 } else {
 const webSearchResult = await searchDatasheetUrl(`${partQuery} ${deviceModel}`);
 if (webSearchResult) {
 aiContext = `Nie udało się pobrać PDF z ${sourceInfo}.\n\nZnalazłem jednak stronę producenta: ${webSearchResult.url}\n\nNa podstawie wyszukiwania mogę powiedzieć, że \`${partQuery}\` to popularny układ. Szczegółowe informacje znajdziesz bezpośrednio na stronie producenta.`;
 finalPdfUrl = webSearchResult.url;
 } else {
 aiContext = `Nie udało się pobrać dokumentacji dla \`${partQuery}\` (${deviceModel}). Spróbuj przesłać PDF bezpośrednio.`;
 }
 }
 } else {
 const webSearchResult = await searchDatasheetUrl(`${partQuery} ${deviceModel}`);
 if (webSearchResult) {
 const base64 = await downloadPdfAsBase64(webSearchResult.url);
 if (base64) {
 // ── R3: PDF hidden content analysis ──
 const pdfAnalysis = extractAndAnalyzePdf(base64);
 pdfSecurityWarning = buildPdfHiddenContentWarning(pdfAnalysis);
 if (pdfAnalysis.isSuspicious) {
 try { await persistAuditToDb(env, { chat_id: message?.chat_id, user_id: message?.user_id, attack_type: "pdf_hidden_content", severity: "high", details: { flags: pdfAnalysis.hiddenContentFlags, warnings: pdfAnalysis.warnings }, action_taken: "flagged_passed" }); } catch { /* non-blocking */ }
 }

 const datasheetSystemPrompt = [
 "Jesteś inżynierem elektronikiem. Odpowiedz na pytanie użytkownika na podstawie datasheet.",
 buildAntiInjectionSystemPrefix(),
 pdfSecurityWarning,
 ].join("\n");

 const visionResp = await callProviderWithFallback(env, buildPromptPayload(
 datasheetSystemPrompt,
 `Pytanie: ${sanitized.safeText}\n\nNazwa części: ${partQuery}\nModel: ${deviceModel}`,
 env,
 { media: [{ data: base64, mime_type: "application/pdf" }], maxTokens: 2000 }
 ));
 aiContext = visionResp.text;
 finalPdfUrl = webSearchResult.url;
 } else {
 aiContext = `Znalazłem stronę producenta dla \`${partQuery}\`: ${webSearchResult.url}\n\nNie udało mi się pobrać PDF automatycznie, ale możesz otworzyć stronę ręcznie.`;
 finalPdfUrl = webSearchResult.url;
 }
 } else {
 aiContext = `Nie znalazłem automatycznie datasheet dla \`${partQuery}\` (${deviceModel}). Spróbuj przesłać PDF bezpośrednio lub podaj inną nazwę/model układu.`;
 }
 }

 await recordRecycledSubmission(env, {
 chat_id: message?.chat_id,
 user_id: message?.user_id,
 message_id: message?.message_id,
 lookup_kind: "datasheet_rag",
 query_text: deviceModel,
 matched_part_name: partQuery,
 matched_part_number: partQuery,
 ingest_source: "datasheet_bot",
 status: "approved",
 raw_payload_json: {
 question: sanitized.safeText,
 answer: aiContext,
 device: deviceModel,
 pdf_url: finalPdfUrl,
 source: sourceInfo,
 pdf_security_flags: pdfSecurityWarning ? "warning_added" : "clean",
 }
 });

 await closeUserSession(env, message.chat_id, message.user_id, "datasheet_wait_question");

 const reply_markup = finalPdfUrl ? {
 inline_keyboard: [
 [{ text: "🌐 Otwórz PDF/Datasheet", url: finalPdfUrl }],
 [{ text: "🔄 Analizuj dalej", callback_data: `datasheet_continue:${partQuery}` }]
 ]
 } : undefined;

 return {
 reply_text: `✅ *Analiza datasheet*\n\n📋 *Część:* \`${partQuery}\`\n📦 *Model:* \`${deviceModel}\`\n\n${aiContext}`,
 reply_markup
 };
}

export async function handleDatasheetContinue(env, message, partQuery) {
  await upsertUserSession(env, message.chat_id, message.user_id, "datasheet_wait_question", null, `${partQuery}|${partQuery}`);
  return {
    reply_text: `💡 Kontynuuję analizę dla *${partQuery}*. O co chcesz zapytać?`
  };
}
