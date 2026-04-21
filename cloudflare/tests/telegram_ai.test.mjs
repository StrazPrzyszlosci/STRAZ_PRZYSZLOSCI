import test from "node:test";
import assert from "node:assert/strict";

import {
  buildIssueBody,
  buildIssueTitle,
  callProviderWithFallback,
  extractJsonObject,
  handleFinalDatasheetRagFinal,
  handleRecycledKnowledgeLookup,
  moderateIssueCandidate,
  recognizeDeviceAndListParts,
  recommendOnboardingRouteFromText,
  redactSensitiveContent,
  routeTelegramIntent,
  sanitizeTelegramReply,
} from "../src/telegram_ai.js";
import { handleTelegramWebhook } from "../src/telegram_issues.js";

function jsonResponse(payload, status = 200) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
    },
  });
}

function withMockedFetch(impl, callback) {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = impl;
  return Promise.resolve()
    .then(callback)
    .finally(() => {
      globalThis.fetch = originalFetch;
    });
}

function createRecycledCatalogDbMock() {
  const recycledDevicesColumns = [
    "id",
    "model",
    "brand",
    "description",
    "teardown_url",
    "created_at",
    "device_category",
    "source_url",
    "donor_rank",
  ].map((name) => ({ name }));
  const recycledPartsColumns = [
    "id",
    "device_id",
    "part_name",
    "species",
    "value",
    "designator",
    "description",
    "created_at",
    "genus",
    "mounting",
    "keywords",
    "kicad_symbol",
    "kicad_footprint",
    "datasheet_url",
    "quantity",
    "source_url",
    "confidence",
  ].map((name) => ({ name }));
  const recycledPartMasterColumns = [
    "id",
    "part_slug",
    "part_number",
    "normalized_part_number",
    "part_name",
    "species",
    "genus",
    "mounting",
    "value",
    "description",
    "keywords",
    "datasheet_url",
    "datasheet_file_id",
    "ipn",
    "category",
    "parameters",
    "kicad_symbol",
    "kicad_footprint",
    "kicad_reference",
  ].map((name) => ({ name }));
  const recycledDevicePartsColumns = [
    "id",
    "device_id",
    "master_part_id",
    "quantity",
    "designator",
    "source_url",
    "confidence",
    "stock_location",
  ].map((name) => ({ name }));

  return {
    prepare(sql) {
      const normalizedSql = String(sql).replace(/\s+/g, " ").trim();
      const statement = {
        async run() {
          return { success: true };
        },
        async first() {
          return null;
        },
        async all() {
          return { results: [] };
        },
      };
      return {
        ...statement,
        bind(...args) {
          return {
            ...statement,
            async first() {
              if (normalizedSql.includes("FROM recycled_devices d")) {
                const query = String(args[0] || "");
                if (/sonoff basic/i.test(query) || /^basic$/i.test(query)) {
                  return {
                    id: 3,
                    model: "Basic",
                    brand: "Sonoff",
                    description: "Popular Wi-Fi relay board and reliable seed donor for ESP8266-based reuse workflows.",
                    teardown_url: "https://tasmota.github.io/docs/devices/Sonoff-Basic/",
                    device_category: "smart_switch",
                    source_url: "https://tasmota.github.io/docs/devices/Sonoff-Basic/",
                    donor_rank: 0.88,
                  };
                }
              }
              return null;
            },
            async all() {
              if (normalizedSql.includes("PRAGMA table_info(recycled_devices)")) {
                return { results: recycledDevicesColumns };
              }
              if (normalizedSql.includes("PRAGMA table_info(recycled_parts)")) {
                return { results: recycledPartsColumns };
              }
              if (normalizedSql.includes("PRAGMA table_info(recycled_part_master)")) {
                return { results: recycledPartMasterColumns };
              }
              if (normalizedSql.includes("PRAGMA table_info(recycled_device_parts)")) {
                return { results: recycledDevicePartsColumns };
              }
              if (
                normalizedSql.includes("FROM recycled_device_parts rdp") &&
                normalizedSql.includes("JOIN recycled_part_master pm")
              ) {
                return {
                  results: [
                    {
                      part_name: "ESP8266EX",
                      species: "IC",
                      value: "",
                      designator: "U1",
                      description: "Highly integrated Wi-Fi SoC commonly reused in automation and telemetry prototypes.",
                      quantity: 1,
                      datasheet_url:
                        "https://www.espressif.com/sites/default/files/documentation/0a-esp8266ex_datasheet_en.pdf",
                      kicad_symbol: "MCU_Espressif:ESP8266EX",
                      kicad_footprint:
                        "Package_DFN_QFN:QFN-32-1EP_5x5mm_P0.5mm_EP3.3x3.3mm",
                      part_number: "ESP8266EX",
                      ipn: "ESP8266EX",
                      category: "wifi_soc",
                      parameters: "{\"WiFi\":\"2.4GHz\"}",
                      datasheet_file_id: "",
                      kicad_reference: "U",
                      stock_location: "",
                    },
                  ],
                };
              }
              if (
                normalizedSql.includes("FROM recycled_parts") &&
                normalizedSql.includes("WHERE device_id = ?")
              ) {
                return {
                  results: [
                    {
                      part_name: "ESP8266EX",
                      species: "IC",
                      value: "",
                      designator: "U1",
                      description: "Highly integrated Wi-Fi SoC commonly reused in automation and telemetry prototypes.",
                      quantity: 1,
                      datasheet_url:
                        "https://www.espressif.com/sites/default/files/documentation/0a-esp8266ex_datasheet_en.pdf",
                      kicad_symbol: "MCU_Espressif:ESP8266EX",
                      kicad_footprint:
                        "Package_DFN_QFN:QFN-32-1EP_5x5mm_P0.5mm_EP3.3x3.3mm",
                    },
                  ],
                };
              }
              if (normalizedSql.includes("FROM recycled_parts p")) {
                const query = String(args[0] || "");
                if (/atmega328p/i.test(query)) {
                  return {
                    results: [
                      {
                        part_name: "ATmega328P",
                        species: "IC",
                        value: "",
                        designator: "U1",
                        description:
                          "8-bit AVR microcontroller frequently reused from Arduino-compatible boards.",
                        quantity: 1,
                        datasheet_url:
                          "https://ww1.microchip.com/downloads/en/DeviceDoc/Atmel-7810-Automotive-Microcontrollers-ATmega328P_Datasheet.pdf",
                        kicad_symbol: "MCU_Microchip_ATmega:ATmega328P-PU",
                        kicad_footprint: "Package_DIP:DIP-28_W7.62mm",
                        device_id: 4,
                        model: "Uno Clone",
                        brand: "Arduino Compatible",
                        device_description:
                          "Seed donor entry for DIP AVR microcontrollers and prototyping support parts.",
                        teardown_url: "",
                      },
                    ],
                  };
                }
              }
              if (normalizedSql.includes("FROM recycled_part_master pm")) {
                const query = String(args[0] || "");
                if (/atmega328p/i.test(query)) {
                  return {
                    results: [
                      {
                        id: 5,
                        part_slug: "atmega328p-pu",
                        part_number: "ATMEGA328P-PU",
                        normalized_part_number: "ATMEGA328P-PU",
                        part_name: "ATmega328P",
                        species: "IC",
                        genus: "microcontroller",
                        mounting: "THT",
                        value: "",
                        description:
                          "8-bit AVR microcontroller frequently reused from Arduino-compatible boards.",
                        keywords: "ATmega328P, AVR, DIP",
                        datasheet_url:
                          "https://ww1.microchip.com/downloads/en/DeviceDoc/Atmel-7810-Automotive-Microcontrollers-ATmega328P_Datasheet.pdf",
                        datasheet_file_id: "",
                        ipn: "ATMEGA328P-PU",
                        category: "mcu",
                        parameters: "{\"Flash\":\"32KB\"}",
                        kicad_symbol: "MCU_Microchip_ATmega:ATmega328P-PU",
                        kicad_footprint: "Package_DIP:DIP-28_W7.62mm",
                        kicad_reference: "U",
                        donor_count: 1,
                      },
                    ],
                  };
                }
              }
              return { results: [] };
            },
          };
        },
      };
    },
  };
}

function createScanFlowDbMock() {
  const recycledDevicesColumns = [
    "id",
    "model",
    "brand",
    "description",
    "teardown_url",
    "created_at",
    "device_category",
    "source_url",
    "donor_rank",
  ].map((name) => ({ name }));
  const recycledPartsColumns = [
    "id",
    "device_id",
    "part_name",
    "species",
    "value",
    "designator",
    "description",
    "created_at",
    "genus",
    "mounting",
    "keywords",
    "kicad_symbol",
    "kicad_footprint",
    "datasheet_url",
    "quantity",
    "source_url",
    "confidence",
    "ipn",
    "category",
    "parameters",
    "datasheet_file_id",
    "kicad_reference",
    "stock_location",
    "master_part_id",
  ].map((name) => ({ name }));
  const recycledPartMasterColumns = [
    "id",
    "part_slug",
    "part_number",
    "normalized_part_number",
    "part_name",
    "species",
    "genus",
    "mounting",
    "value",
    "description",
    "keywords",
    "datasheet_url",
    "datasheet_file_id",
    "ipn",
    "category",
    "parameters",
    "kicad_symbol",
    "kicad_footprint",
    "kicad_reference",
  ].map((name) => ({ name }));
  const recycledDevicePartsColumns = [
    "id",
    "device_id",
    "master_part_id",
    "quantity",
    "designator",
    "source_url",
    "confidence",
    "stock_location",
  ].map((name) => ({ name }));

  const state = {
    sessions: new Map(),
    chatLimits: new Map(),
    parts: [
      {
        id: 1,
        part_slug: "atmega328p-pu",
        part_number: "ATMEGA328P-PU",
        normalized_part_number: "ATMEGA328P-PU",
        part_name: "ATmega328P",
        species: "IC",
        genus: "microcontroller",
        mounting: "THT",
        value: "",
        description: "8-bit AVR microcontroller frequently reused from Arduino-compatible boards.",
        keywords: "ATmega328P, AVR, DIP",
        datasheet_url: "https://example.com/atmega328p.pdf",
        datasheet_file_id: "",
        ipn: "ATMEGA328P-PU",
        category: "mcu",
        parameters: "{\"Flash\":\"32KB\"}",
        kicad_symbol: "MCU_Microchip_ATmega:ATmega328P-PU",
        kicad_footprint: "Package_DIP:DIP-28_W7.62mm",
        kicad_reference: "U",
      },
    ],
    devices: [
      {
        id: 10,
        model: "Uno Clone",
        brand: "Arduino Compatible",
        description: "Seed donor entry for DIP AVR microcontrollers.",
        teardown_url: "",
        created_at: new Date().toISOString(),
        device_category: "dev_board",
        source_url: "",
        donor_rank: 0.7,
      },
      {
        id: 20,
        model: "ThinkPad T480",
        brand: "Lenovo",
        description: "Laptop donor",
        teardown_url: "",
        created_at: new Date().toISOString(),
        device_category: "laptop",
        source_url: "",
        donor_rank: 0.8,
      },
    ],
    deviceParts: [
      {
        id: 1,
        device_id: 10,
        master_part_id: 1,
        quantity: 1,
        designator: "U1",
        source_url: "",
        confidence: 0.9,
        stock_location: "",
      },
    ],
    nextPartId: 2,
    nextDeviceId: 21,
    nextDevicePartId: 2,
  };

  const normalizeSql = (sql) => String(sql).replace(/\s+/g, " ").trim();
  const normalizePartNumber = (value) =>
    String(value || "")
      .trim()
      .toUpperCase()
      .replace(/\s+/g, "")
      .replace(/[^A-Z0-9._+\-/]/g, "");
  const sessionKey = (chatId, userId, sessionType) => `${chatId}:${userId}:${sessionType}`;
  const getPartById = (id) => state.parts.find((part) => part.id === Number(id)) || null;
  const getDeviceById = (id) => state.devices.find((device) => device.id === Number(id)) || null;
  const donorCount = (partId) => new Set(state.deviceParts.filter((row) => row.master_part_id === partId).map((row) => row.device_id)).size;
  const searchPartMatches = (query) => {
    const normalizedQuery = String(query || "").trim();
    const normalizedNumber = normalizePartNumber(normalizedQuery);
    return state.parts
      .filter((part) => {
        const keywords = String(part.keywords || "").toLowerCase();
        return (
          normalizePartNumber(part.normalized_part_number || part.part_number) === normalizedNumber ||
          String(part.part_number || "").toLowerCase() === normalizedQuery.toLowerCase() ||
          String(part.part_name || "").toLowerCase() === normalizedQuery.toLowerCase() ||
          String(part.part_name || "").toLowerCase().includes(normalizedQuery.toLowerCase()) ||
          String(part.part_number || "").toLowerCase().includes(normalizedQuery.toLowerCase()) ||
          keywords.includes(normalizedQuery.toLowerCase())
        );
      })
      .map((part) => ({ ...part, donor_count: donorCount(part.id) }));
  };
  const searchPartDonors = (query) => {
    const matches = searchPartMatches(query);
    if (!matches.length) {
      return [];
    }
    const targetIds = new Set(matches.map((part) => part.id));
    return state.deviceParts
      .filter((row) => targetIds.has(row.master_part_id))
      .map((row) => {
        const part = getPartById(row.master_part_id);
        const device = getDeviceById(row.device_id);
        return {
          part_name: part.part_name,
          species: part.species,
          value: part.value,
          designator: row.designator,
          description: part.description,
          quantity: row.quantity,
          datasheet_url: part.datasheet_url,
          kicad_symbol: part.kicad_symbol,
          kicad_footprint: part.kicad_footprint,
          part_number: part.part_number,
          device_id: device.id,
          model: device.model,
          brand: device.brand,
          device_description: device.description,
          teardown_url: device.teardown_url,
        };
      });
  };

  function handleRun(normalizedSql, args) {
    if (normalizedSql.startsWith("CREATE TABLE") || normalizedSql.startsWith("CREATE INDEX")) {
      return { success: true };
    }
    if (normalizedSql.includes("INSERT INTO telegram_user_sessions")) {
      const [chatId, userId, sessionType, activeDeviceId, activeDeviceName, createdAt, updatedAt] = args;
      state.sessions.set(sessionKey(chatId, userId, sessionType), {
        chat_id: chatId,
        user_id: userId,
        session_type: sessionType,
        active_device_id: activeDeviceId,
        active_device_name: activeDeviceName,
        status: "active",
        created_at: createdAt,
        updated_at: updatedAt,
      });
      return { success: true };
    }
    if (normalizedSql.includes("UPDATE telegram_user_sessions SET status = 'closed'") && normalizedSql.includes("session_type = ?")) {
      const [updatedAt, chatId, userId, sessionType] = args;
      const key = sessionKey(chatId, userId, sessionType);
      const row = state.sessions.get(key);
      if (row) {
        state.sessions.set(key, { ...row, status: "closed", updated_at: updatedAt });
      }
      return { success: true };
    }
    if (normalizedSql.includes("UPDATE telegram_user_sessions SET status = 'closed'") && !normalizedSql.includes("session_type = ?")) {
      const [updatedAt, chatId, userId] = args;
      for (const [key, row] of state.sessions.entries()) {
        if (row.chat_id === chatId && row.user_id === userId) {
          state.sessions.set(key, { ...row, status: "closed", updated_at: updatedAt });
        }
      }
      return { success: true };
    }
    if (normalizedSql.includes("INSERT INTO telegram_chat_limits")) {
      const [limitKey, bucketName, windowStartedAt, requestCount, lastRequestAt] = args;
      state.chatLimits.set(limitKey, {
        limit_key: limitKey,
        bucket_name: bucketName,
        window_started_at: windowStartedAt,
        request_count: requestCount,
        last_request_at: lastRequestAt,
      });
      return { success: true };
    }
    if (normalizedSql.includes("INSERT INTO telegram_chat_messages")) {
      return { success: true };
    }
    if (normalizedSql.includes("INSERT INTO recycled_part_master")) {
      const [
        partSlug,
        partNumber,
        normalizedPartNumber,
        partName,
        species,
        genus,
        mounting,
        value,
        description,
        keywords,
        datasheetUrl,
        datasheetFileId,
        ipn,
        category,
        parameters,
        kicadSymbol,
        kicadFootprint,
        kicadReference,
      ] = args;
      const id = state.nextPartId++;
      state.parts.push({
        id,
        part_slug: partSlug,
        part_number: partNumber,
        normalized_part_number: normalizedPartNumber,
        part_name: partName,
        species,
        genus,
        mounting,
        value,
        description,
        keywords,
        datasheet_url: datasheetUrl,
        datasheet_file_id: datasheetFileId,
        ipn,
        category,
        parameters,
        kicad_symbol: kicadSymbol,
        kicad_footprint: kicadFootprint,
        kicad_reference: kicadReference,
      });
      return { meta: { last_row_id: id } };
    }
    if (normalizedSql.includes("UPDATE recycled_part_master SET")) {
      const id = Number(args[args.length - 1]);
      const existing = getPartById(id);
      if (existing) {
        const [
          partSlug,
          partNumber,
          normalizedPartNumber,
          partName,
          species,
          genus,
          mounting,
          value,
          description,
          keywords,
          datasheetUrl,
          datasheetFileId,
          ipn,
          category,
          parameters,
          kicadSymbol,
          kicadFootprint,
          kicadReference,
        ] = args;
        Object.assign(existing, {
          part_slug: partSlug,
          part_number: partNumber,
          normalized_part_number: normalizedPartNumber,
          part_name: partName,
          species,
          genus,
          mounting,
          value,
          description,
          keywords,
          datasheet_url: datasheetUrl,
          datasheet_file_id: datasheetFileId,
          ipn,
          category,
          parameters,
          kicad_symbol: kicadSymbol,
          kicad_footprint: kicadFootprint,
          kicad_reference: kicadReference,
        });
      }
      return { success: true };
    }
    if (normalizedSql.includes("INSERT INTO recycled_devices")) {
      const [model, brand, description, teardownUrl, createdAt, deviceCategory, sourceUrl, donorRank] = args;
      const id = state.nextDeviceId++;
      state.devices.push({
        id,
        model,
        brand,
        description,
        teardown_url: teardownUrl,
        created_at: createdAt,
        device_category: deviceCategory,
        source_url: sourceUrl,
        donor_rank: donorRank,
      });
      return { meta: { last_row_id: id } };
    }
    if (normalizedSql.includes("INSERT INTO recycled_device_parts")) {
      const [deviceId, masterPartId, quantity, designator, sourceUrl, confidence, stockLocation] = args;
      const id = state.nextDevicePartId++;
      state.deviceParts.push({
        id,
        device_id: Number(deviceId),
        master_part_id: Number(masterPartId),
        quantity,
        designator,
        source_url: sourceUrl,
        confidence,
        stock_location: stockLocation,
      });
      return { meta: { last_row_id: id } };
    }
    if (normalizedSql.includes("UPDATE recycled_device_submissions")) {
      return { success: true };
    }
    return { success: true };
  }

  function handleFirst(normalizedSql, args) {
    if (normalizedSql.includes("FROM telegram_chat_limits")) {
      return state.chatLimits.get(args[0]) || null;
    }
    if (normalizedSql.includes("FROM telegram_user_sessions")) {
      const [chatId, userId, sessionType] = args;
      const row = state.sessions.get(sessionKey(chatId, userId, sessionType));
      return row && row.status === "active" ? row : null;
    }
    if (normalizedSql.includes("SELECT * FROM recycled_part_master WHERE id = ?")) {
      return getPartById(args[0]);
    }
    if (normalizedSql.includes("SELECT * FROM recycled_part_master WHERE LOWER(COALESCE(normalized_part_number")) {
      const normalizedNumber = String(args[0] || "").toUpperCase();
      return state.parts.find((part) => String(part.normalized_part_number || "").toUpperCase() === normalizedNumber) || null;
    }
    if (normalizedSql.includes("SELECT * FROM recycled_part_master WHERE part_slug = ?")) {
      return state.parts.find((part) => part.part_slug === args[0]) || null;
    }
    if (normalizedSql.includes("FROM recycled_devices WHERE LOWER(model) = LOWER(?)")) {
      return state.devices.find((device) => String(device.model).toLowerCase() === String(args[0] || "").toLowerCase()) || null;
    }
    if (normalizedSql.includes("FROM recycled_devices WHERE id = ? LIMIT 1") || normalizedSql.includes("FROM recycled_devices WHERE id = ?")) {
      return getDeviceById(args[0]);
    }
    if (normalizedSql.includes("SELECT id FROM recycled_device_parts")) {
      const [deviceId, masterPartId, designator] = args;
      const row = state.deviceParts.find(
        (item) =>
          item.device_id === Number(deviceId) &&
          item.master_part_id === Number(masterPartId) &&
          String(item.designator || "") === String(designator || "")
      );
      return row ? { id: row.id } : null;
    }
    if (normalizedSql.includes("SELECT brand, model FROM recycled_devices WHERE id = ?")) {
      const device = getDeviceById(args[0]);
      return device ? { brand: device.brand, model: device.model } : null;
    }
    return null;
  }

  function handleAll(normalizedSql, args) {
    if (normalizedSql.includes("PRAGMA table_info(recycled_devices)")) {
      return { results: recycledDevicesColumns };
    }
    if (normalizedSql.includes("PRAGMA table_info(recycled_parts)")) {
      return { results: recycledPartsColumns };
    }
    if (normalizedSql.includes("PRAGMA table_info(recycled_part_master)")) {
      return { results: recycledPartMasterColumns };
    }
    if (normalizedSql.includes("PRAGMA table_info(recycled_device_parts)")) {
      return { results: recycledDevicePartsColumns };
    }
    if (normalizedSql.includes("FROM recycled_part_master pm") && normalizedSql.includes("COUNT(DISTINCT rdp.device_id) AS donor_count")) {
      return { results: searchPartMatches(args[0]) };
    }
    if (normalizedSql.includes("FROM recycled_part_master pm") && normalizedSql.includes("JOIN recycled_device_parts rdp")) {
      return { results: searchPartDonors(args[0]) };
    }
    return { results: [] };
  }

  return {
    state,
    prepare(sql) {
      const normalizedSql = normalizeSql(sql);
      return {
        async run() {
          return handleRun(normalizedSql, []);
        },
        async first() {
          return handleFirst(normalizedSql, []);
        },
        async all() {
          return handleAll(normalizedSql, []);
        },
        bind(...args) {
          return {
            async run() {
              return handleRun(normalizedSql, args);
            },
            async first() {
              return handleFirst(normalizedSql, args);
            },
            async all() {
              return handleAll(normalizedSql, args);
            },
          };
        },
      };
    },
  };
}

function createTelegramFlowHarness(options = {}) {
  const db = options.db || createScanFlowDbMock();
  const sentMessages = [];
  const callbackAnswers = [];

  const env = {
    DB: db,
    TELEGRAM_AI_ENABLED: "true",
    TELEGRAM_ISSUES_ENABLED: "true",
    TELEGRAM_ALLOWED_CHAT_IDS: "*",
    TELEGRAM_BOT_TOKEN: "telegram-token",
    TELEGRAM_AI_PRIMARY_PROVIDER: "google",
    TELEGRAM_AI_FALLBACK_PROVIDER: "google",
    TELEGRAM_AI_GOOGLE_MODEL: "gemma-3-27b-it",
    TELEGRAM_AI_REQUESTS_PER_5_MIN: "50",
    TELEGRAM_AI_REQUESTS_PER_DAY: "500",
    GEMINI_API_KEY: "google-key",
    ...options.env,
  };

  const fetchImpl = async (url, init = {}) => {
    const urlString = String(url);
    if (urlString.includes("api.telegram.org/bottelegram-token/sendMessage")) {
      sentMessages.push(JSON.parse(init.body));
      return jsonResponse({ ok: true });
    }
    if (urlString.includes("api.telegram.org/bottelegram-token/answerCallbackQuery")) {
      callbackAnswers.push(JSON.parse(init.body));
      return jsonResponse({ ok: true });
    }
    if (urlString.includes("api.telegram.org/bottelegram-token/editMessageReplyMarkup")) {
      return jsonResponse({ ok: true });
    }
    if (urlString.includes("api.telegram.org/bottelegram-token/getFile")) {
      const fileId = new URL(urlString).searchParams.get("file_id");
      return jsonResponse({ ok: true, result: { file_path: `${fileId}.jpg` } });
    }
    if (urlString.includes("api.telegram.org/file/bottelegram-token/")) {
      return new Response(Uint8Array.from([1, 2, 3]), { status: 200 });
    }
    if (urlString.includes("generativelanguage.googleapis.com")) {
      const bodyText = String(init.body || "");
      let text = '{"decision":"accept","reason_code":"ok","reason_text":"OK"}';
      if (bodyText.includes("technicznym weryfikatorem")) {
        text = "SENSOWNE";
      } else if (bodyText.includes("Rozpoznaj część ze zdjęcia")) {
        text = options.partRecognitionResponse || '{"part_name":"Sterownik silnika","part_number":"DRV-7788","description":"Układ sterownika silnika.","category":"driver","parameters":{"Voltage":"12V"},"confidence":0.91}';
      } else if (bodyText.includes("Rozpoznaj model urządzenia ze zdjęcia")) {
        text = options.deviceRecognitionResponse || '{"brand":"Lenovo","model":"ThinkPad T480","confidence":0.88}';
      } else if (bodyText.includes("lokalnej bazy części reuse")) {
        text = options.partQaResponse || "To mikrokontroler AVR 8-bit. W bazie mam też informację, że występuje w donorze Arduino Compatible Uno Clone.";
      }
      return jsonResponse({
        candidates: [
          {
            content: {
              parts: [{ text }],
            },
          },
        ],
      });
    }
    if (urlString.startsWith("https://www.") || urlString.startsWith("https://www.alldatasheet.com") || urlString.startsWith("https://www.google.com")) {
      return new Response("", { status: 404, headers: { "content-type": "text/html" } });
    }
    throw new Error(`Unexpected URL: ${urlString}`);
  };

  async function sendWebhook(payload) {
    const request = new Request("https://example.workers.dev/integrations/telegram/webhook", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(payload),
    });
    return handleTelegramWebhook(request, env);
  }

  return {
    env,
    db,
    sentMessages,
    callbackAnswers,
    fetchImpl,
    sendWebhook,
  };
}

test("routeTelegramIntent keeps onboarding separate from issues", () => {
  assert.deepEqual(routeTelegramIntent("Pomysl: zróbmy panel porównań").intent, "issue");
  assert.deepEqual(routeTelegramIntent("Gdzie mogę pomóc jako backendowiec?").intent, "onboarding");
  assert.deepEqual(routeTelegramIntent("Opowiedz mi więcej o inicjatywie").intent, "chat");
});

test("routeTelegramIntent detects recycled-parts lookup from text", () => {
  assert.equal(routeTelegramIntent("ATmega328P").intent, "device_lookup");
  assert.equal(routeTelegramIntent({ text: "Jakie części są w Sonoff Basic?" }).intent, "device_lookup");
});

test("recommendOnboardingRouteFromText finds data path without hardware", () => {
  const result = recommendOnboardingRouteFromText(
    "Nie mam własnego sprzętu, ale znam backend, API, walidację i mogę pomagać w architekturze danych."
  );
  assert.ok(result);
  assert.equal(result.route.route_id, "data_architecture_without_hardware");
  assert.equal(result.should_suggest_provider_path, true);
});

test("buildIssueTitle keeps original message trimmed without AI rewrite", () => {
  const title = buildIssueTitle({
    content:
      "To jest bardzo długi oryginalny wpis użytkownika, który powinien zostać przycięty, ale bez przepisywania przez AI i bez dodawania prefiksu.",
  });
  assert.equal(title.startsWith("To jest bardzo długi oryginalny wpis użytkownika"), true);
  assert.equal(title.length, 96);
});

test("buildIssueBody stores original and edited text in separate sections", () => {
  const body = buildIssueBody(
    {
      username: "tester",
      chat_id: "123",
      message_id: "7",
      chat_type: "private",
    },
    {
      label: "pomysł",
      content: "surowa tresc telegramowa",
    },
    {
      edited_description: "Uporządkowany opis bez zmiany sensu.",
      additional_context: "Warto powiązać to z istniejącym projektem.",
    }
  );

  assert.match(body, /## Oryginalna wiadomość/);
  assert.match(body, /surowa tresc telegramowa/);
  assert.match(body, /## Zredagowany opis/);
  assert.match(body, /Uporządkowany opis bez zmiany sensu\./);
  assert.match(body, /## Dodatkowe objaśnienie AI/);
});

test("extractJsonObject parses fenced JSON payloads", () => {
  const parsed = extractJsonObject('```json\n{"decision":"accept","reason_code":"ok","reason_text":"OK"}\n```');
  assert.equal(parsed.decision, "accept");
  assert.equal(parsed.reason_code, "ok");
});

test("redaction hides tokens and secret variable names", () => {
  const redacted = redactSensitiveContent(
    "Sekret AIzaSyBardzoTajny123456789012345 i GITHUB_TOKEN oraz Bearer abcdefghijklmnopqrstuvwxyz0123456789"
  );
  assert.doesNotMatch(redacted, /AIza/);
  assert.doesNotMatch(redacted, /GITHUB_TOKEN/);
  assert.doesNotMatch(redacted, /Bearer\s+[A-Za-z0-9._-]{20,}/);
});

test("sanitizeTelegramReply clamps long responses", () => {
  const text = "A".repeat(4000);
  const sanitized = sanitizeTelegramReply(text, { TELEGRAM_AI_MAX_REPLY_CHARS: "200" });
  assert.ok(sanitized.length <= 220);
  assert.match(sanitized, /\[odpowiedź skrócona\]/);
});

test("moderateIssueCandidate returns structured decision from Google provider", async () => {
  const env = {
    TELEGRAM_AI_ENABLED: "true",
    TELEGRAM_AI_PRIMARY_PROVIDER: "google",
    TELEGRAM_AI_FALLBACK_PROVIDER: "nvidia",
    TELEGRAM_AI_GOOGLE_MODEL: "gemma-3-27b-it",
    GEMINI_API_KEY: "test-key",
  };

  const result = await moderateIssueCandidate(
    env,
    {
      kind: "idea",
      label: "pomysł",
      content: "Zróbmy prosty dashboard dla porównań przypadków.",
    },
    {
      chat_id: "123",
      user_id: "456",
      message_id: "9",
      text: "Pomysl: Zróbmy prosty dashboard dla porównań przypadków.",
    },
    [],
    {
      fetchImpl: async () =>
        jsonResponse({
          candidates: [
            {
              content: {
                parts: [
                  {
                    text: '{"decision":"accept","reason_code":"ok","reason_text":"Treść jest konkretna i merytoryczna."}',
                  },
                ],
              },
            },
          ],
        }),
    }
  );

  assert.equal(result.decision, "accept");
  assert.equal(result.reason_code, "ok");
});

test("callProviderWithFallback switches from Google to NVIDIA on 429", async () => {
  const env = {
    TELEGRAM_AI_PRIMARY_PROVIDER: "google",
    TELEGRAM_AI_FALLBACK_PROVIDER: "nvidia",
    TELEGRAM_AI_GOOGLE_MODEL: "gemma-3-27b-it",
    TELEGRAM_AI_NVIDIA_MODEL: "google/gemma-4-31b-it",
    GEMINI_API_KEY: "google-key",
    NVIDIA_API_KEY: "nvidia-key",
  };

  const calls = [];
  const response = await callProviderWithFallback(
    env,
    {
      systemInstruction: "system",
      userPrompt: "user",
      maxTokens: 100,
      temperature: 0.2,
      responseMimeType: "application/json",
    },
    {
      fetchImpl: async (url) => {
        calls.push(url);
        if (url.includes("generativelanguage.googleapis.com")) {
          return jsonResponse(
            {
              error: {
                message: "rate limited",
              },
            },
            429
          );
        }
        return jsonResponse({
          choices: [
            {
              message: {
                content: '{"decision":"accept"}',
              },
            },
          ],
        });
      },
    }
  );

  assert.equal(response.provider_name, "nvidia");
  assert.equal(calls.length, 2);
  assert.ok(calls[0].includes("generativelanguage.googleapis.com"));
  assert.ok(calls[1].includes("integrate.api.nvidia.com"));
});

test("callProviderWithFallback retries Google without developer instruction when model rejects it", async () => {
  const env = {
    TELEGRAM_AI_PRIMARY_PROVIDER: "google",
    TELEGRAM_AI_FALLBACK_PROVIDER: "nvidia",
    TELEGRAM_AI_GOOGLE_MODEL: "gemma-3-27b-it",
    GEMINI_API_KEY: "google-key",
  };

  const requestBodies = [];
  const response = await callProviderWithFallback(
    env,
    {
      systemInstruction: "system guidance",
      userPrompt: "user question",
      maxTokens: 100,
      temperature: 0.2,
      responseMimeType: "application/json",
    },
    {
      fetchImpl: async (_url, init = {}) => {
        requestBodies.push(JSON.parse(init.body));
        if (requestBodies.length === 1) {
          return jsonResponse(
            {
              error: {
                message: "Developer instruction is not enabled for models/gemma-3-27b-it",
              },
            },
            400
          );
        }

        return jsonResponse({
          candidates: [
            {
              content: {
                parts: [
                  {
                    text: '{"decision":"accept"}',
                  },
                ],
              },
            },
          ],
        });
      },
    }
  );

  assert.equal(response.provider_name, "google");
  assert.equal(requestBodies.length, 2);
  const firstPromptText = requestBodies[0].contents[0].parts.map((part) => part.text || "").join(" ");
  const retriedPromptText = requestBodies[1].contents[0].parts.map((part) => part.text || "").join(" ");
  assert.match(firstPromptText, /system guidance/);
  assert.equal(requestBodies[1].systemInstruction, undefined);
  assert.match(retriedPromptText, /system guidance/);
  assert.match(retriedPromptText, /user question/);
});

test("callProviderWithFallback falls back to NVIDIA when Google still rejects developer instruction mode", async () => {
  const env = {
    TELEGRAM_AI_PRIMARY_PROVIDER: "google",
    TELEGRAM_AI_FALLBACK_PROVIDER: "nvidia",
    TELEGRAM_AI_GOOGLE_MODEL: "gemma-3-27b-it",
    TELEGRAM_AI_NVIDIA_MODEL: "google/gemma-4-31b-it",
    GEMINI_API_KEY: "google-key",
    NVIDIA_API_KEY: "nvidia-key",
  };

  const calls = [];
  const response = await callProviderWithFallback(
    env,
    {
      systemInstruction: "system guidance",
      userPrompt: "user question",
      maxTokens: 100,
      temperature: 0.2,
      responseMimeType: "application/json",
    },
    {
      fetchImpl: async (url, init = {}) => {
        calls.push({
          url,
          body: init.body ? JSON.parse(init.body) : null,
        });
        if (url.includes("generativelanguage.googleapis.com")) {
          return jsonResponse(
            {
              error: {
                message: "Developer instruction is not enabled for models/gemma-3-27b-it",
              },
            },
            400
          );
        }

        return jsonResponse({
          choices: [
            {
              message: {
                content: '{"decision":"accept","reason_code":"ok","reason_text":"Przyjęte przez fallback."}',
              },
            },
          ],
        });
      },
    }
  );

  assert.equal(response.provider_name, "nvidia");
  assert.equal(calls.length, 3);
  assert.ok(calls[0].url.includes("generativelanguage.googleapis.com"));
  assert.ok(calls[1].url.includes("generativelanguage.googleapis.com"));
  assert.ok(calls[2].url.includes("integrate.api.nvidia.com"));
});

test("handleRecycledKnowledgeLookup returns device catalog entry from local DB", async () => {
  const response = await handleRecycledKnowledgeLookup(
    {
      DB: createRecycledCatalogDbMock(),
    },
    {
      chat_id: "4",
      user_id: "3",
      message_id: "2",
      text: "Jakie części są w Sonoff Basic?",
    }
  );

  assert.equal(response.provider_name, "local");
  assert.match(response.reply_text, /Sonoff Basic/);
  assert.match(response.reply_text, /ESP8266EX/);
});

test("handleRecycledKnowledgeLookup returns donor devices for part query", async () => {
  const response = await handleRecycledKnowledgeLookup(
    {
      DB: createRecycledCatalogDbMock(),
    },
    {
      chat_id: "7",
      user_id: "8",
      message_id: "9",
      text: "ATmega328P",
    }
  );

  assert.equal(response.provider_name, "local");
  assert.match(response.reply_text, /ATmega328P/);
  assert.match(response.reply_text, /Arduino Compatible Uno Clone/);
});

test("recognizeDeviceAndListParts sends inline media to Google provider", async () => {
  const env = {
    DB: null,
    GEMINI_API_KEY: "google-key",
    TELEGRAM_AI_PRIMARY_PROVIDER: "google",
    TELEGRAM_AI_FALLBACK_PROVIDER: "nvidia",
    TELEGRAM_AI_GOOGLE_MODEL: "gemma-3-27b-it",
  };

  let requestBody = null;
  await withMockedFetch(async (url, init = {}) => {
    if (url.includes("generativelanguage.googleapis.com")) {
      requestBody = JSON.parse(init.body);
      return jsonResponse({
        candidates: [
          {
            content: {
              parts: [
                {
                  text: '{"brand":"Sonoff","model":"Basic","confidence":0.95}',
                },
              ],
            },
          },
        ],
      });
    }
    throw new Error(`Unexpected URL: ${url}`);
  }, async () => {
    const response = await recognizeDeviceAndListParts(
      env,
      { mime_type: "image/jpeg" },
      "AQID"
    );

    assert.ok(
      requestBody.contents[0].parts.some(
        (part) => part.inline_data?.mime_type === "image/jpeg" && part.inline_data?.data === "AQID"
      )
    );
    assert.match(response.reply_text, /Sonoff Basic/);
  });
});

test("handleTelegramWebhook routes onboarding without creating GitHub issue", async () => {
  const env = {
    DB: null,
    TELEGRAM_AI_ENABLED: "true",
    TELEGRAM_ISSUES_ENABLED: "true",
    TELEGRAM_ALLOWED_CHAT_IDS: "*",
    TELEGRAM_BOT_TOKEN: "telegram-token",
    GEMINI_API_KEY: "google-key",
    TELEGRAM_AI_PRIMARY_PROVIDER: "google",
    TELEGRAM_AI_FALLBACK_PROVIDER: "nvidia",
  };
  const calls = [];

  await withMockedFetch(async (url, init = {}) => {
    calls.push(url);
    if (url.includes("api.telegram.org")) {
      return jsonResponse({ ok: true });
    }
    if (url.includes("generativelanguage.googleapis.com")) {
      return jsonResponse({
        candidates: [
          {
            content: {
              parts: [
                {
                  text: "Rekomendowana ścieżka: API, adaptery i integracja danych.\nPierwszy materiał: https://github.com/StrazPrzyszlosci/STRAZ_PRZYSZLOSCI/blob/main/docs/PRZYKLADY_GOTOWEGO_KODU.md\nPierwsze zadania: issue:aq-09, issue:aq-13",
                },
              ],
            },
          },
        ],
      });
    }
    throw new Error(`Unexpected URL: ${url}`);
  }, async () => {
    const request = new Request("https://example.workers.dev/integrations/telegram/webhook", {
      method: "POST",
      headers: {
        "content-type": "application/json",
      },
      body: JSON.stringify({
        update_id: 1,
        message: {
          message_id: 2,
          from: { id: 3, username: "tester" },
          chat: { id: 4, type: "private" },
          text: "Gdzie mogę pomóc, jeśli znam backend i API?",
        },
      }),
    });
    const response = await handleTelegramWebhook(request, env);
    const payload = await response.json();

    assert.equal(payload.results[0].status, "onboarding_replied");
    assert.equal(calls.some((url) => String(url).includes("/repos/")), false);
  });
});

test("handleTelegramWebhook routes recycled-parts lookup without AI provider call", async () => {
  const env = {
    DB: null,
    TELEGRAM_AI_ENABLED: "true",
    TELEGRAM_ISSUES_ENABLED: "true",
    TELEGRAM_ALLOWED_CHAT_IDS: "*",
    TELEGRAM_BOT_TOKEN: "telegram-token",
  };
  const calls = [];

  await withMockedFetch(async (url) => {
    calls.push(url);
    if (url.includes("api.telegram.org")) {
      return jsonResponse({ ok: true });
    }
    throw new Error(`Unexpected URL: ${url}`);
  }, async () => {
    const request = new Request("https://example.workers.dev/integrations/telegram/webhook", {
      method: "POST",
      headers: {
        "content-type": "application/json",
      },
      body: JSON.stringify({
        update_id: 1,
        message: {
          message_id: 2,
          from: { id: 3, username: "tester" },
          chat: { id: 4, type: "private" },
          text: "ATmega328P",
        },
      }),
    });
    const response = await handleTelegramWebhook(request, env);
    const payload = await response.json();

    assert.equal(payload.results[0].status, "lookup_replied");
    assert.equal(
      calls.some((url) => String(url).includes("generativelanguage.googleapis.com")),
      false
    );
  });
});

test("handleTelegramWebhook creates issue after accepted moderation", async () => {
  const env = {
    DB: null,
    TELEGRAM_AI_ENABLED: "true",
    TELEGRAM_ISSUES_ENABLED: "true",
    TELEGRAM_ISSUES_DRY_RUN: "false",
    TELEGRAM_ALLOWED_CHAT_IDS: "*",
    TELEGRAM_BOT_TOKEN: "telegram-token",
    GEMINI_API_KEY: "google-key",
    GITHUB_TOKEN: "github-token",
    GITHUB_REPO_OWNER: "StrazPrzyszlosci",
    GITHUB_REPO_NAME: "STRAZ_PRZYSZLOSCI",
  };
  const calls = [];
  let googleCall = 0;

  await withMockedFetch(async (url, init = {}) => {
    calls.push(url);
    if (url.includes("api.telegram.org")) {
      return jsonResponse({ ok: true });
    }
    if (url.includes("generativelanguage.googleapis.com")) {
      googleCall += 1;
      if (googleCall === 1) {
        return jsonResponse({
          candidates: [
            {
              content: {
                parts: [
                  {
                    text: '{"decision":"accept","reason_code":"ok","reason_text":"Merytoryczne zgłoszenie."}',
                  },
                ],
              },
            },
          ],
        });
      }
      return jsonResponse({
        candidates: [
          {
            content: {
              parts: [
                {
                  text: '{"edited_description":"Uporządkowany opis pomysłu.","additional_context":"Może być powiązane z dokumentacją adapterów."}',
                },
              ],
            },
          },
        ],
      });
    }
    if (url.includes("api.github.com/repos/StrazPrzyszlosci/STRAZ_PRZYSZLOSCI/issues")) {
      const draft = JSON.parse(init.body);
      assert.equal(draft.title, "Zróbmy prosty dashboard porównujący przypadki.");
      assert.match(draft.body, /## Oryginalna wiadomość/);
      assert.match(draft.body, /## Zredagowany opis/);
      return jsonResponse({
        number: 321,
        html_url: "https://github.com/StrazPrzyszlosci/STRAZ_PRZYSZLOSCI/issues/321",
      });
    }
    throw new Error(`Unexpected URL: ${url}`);
  }, async () => {
    const request = new Request("https://example.workers.dev/integrations/telegram/webhook", {
      method: "POST",
      headers: {
        "content-type": "application/json",
      },
      body: JSON.stringify({
        update_id: 1,
        message: {
          message_id: 2,
          from: { id: 3, username: "tester" },
          chat: { id: 4, type: "private" },
          text: "Pomysl: Zróbmy prosty dashboard porównujący przypadki.",
        },
      }),
    });
    const response = await handleTelegramWebhook(request, env);
    const payload = await response.json();

    assert.equal(payload.results[0].status, "created");
    assert.equal(calls.some((url) => String(url).includes("api.github.com/repos/StrazPrzyszlosci/STRAZ_PRZYSZLOSCI/issues")), true);
  });
});

test("handleTelegramWebhook rejects off-topic issue without GitHub call", async () => {
  const env = {
    DB: null,
    TELEGRAM_AI_ENABLED: "true",
    TELEGRAM_ISSUES_ENABLED: "true",
    TELEGRAM_ISSUES_DRY_RUN: "false",
    TELEGRAM_ALLOWED_CHAT_IDS: "*",
    TELEGRAM_BOT_TOKEN: "telegram-token",
    GEMINI_API_KEY: "google-key",
  };
  const calls = [];

  await withMockedFetch(async (url) => {
    calls.push(url);
    if (url.includes("api.telegram.org")) {
      return jsonResponse({ ok: true });
    }
    if (url.includes("generativelanguage.googleapis.com")) {
      return jsonResponse({
        candidates: [
          {
            content: {
              parts: [
                {
                  text: '{"decision":"reject_off_topic","reason_code":"off_topic","reason_text":"Treść nie dotyczy inicjatywy ani repozytorium."}',
                },
              ],
            },
          },
        ],
      });
    }
    throw new Error(`Unexpected URL: ${url}`);
  }, async () => {
    const request = new Request("https://example.workers.dev/integrations/telegram/webhook", {
      method: "POST",
      headers: {
        "content-type": "application/json",
      },
      body: JSON.stringify({
        update_id: 1,
        message: {
          message_id: 2,
          from: { id: 3, username: "tester" },
          chat: { id: 4, type: "private" },
          text: "Pomysl: sprzedam używany rower.",
        },
      }),
    });
    const response = await handleTelegramWebhook(request, env);
    const payload = await response.json();

    assert.equal(payload.results[0].status, "reject_off_topic");
    assert.equal(calls.some((url) => String(url).includes("api.github.com/repos/")), false);
  });
});

test("menu_scan callback shows new submenu for scan flow", async () => {
  const harness = createTelegramFlowHarness();

  await withMockedFetch(harness.fetchImpl, async () => {
    const response = await harness.sendWebhook({
      callback_query: {
        id: "cb-menu-scan",
        from: { id: 3 },
        message: {
          message_id: 20,
          chat: { id: 4, type: "private" },
        },
        data: "menu_scan",
      },
    });
    const payload = await response.json();

    assert.equal(payload.status, "ok");
    assert.match(harness.sentMessages.at(-1).text, /Prześlij mi zdjęcie elementu elektronicznego/);
    assert.deepEqual(
      harness.sentMessages.at(-1).reply_markup.inline_keyboard[0][0].callback_data,
      "scan_part_start"
    );
    assert.deepEqual(
      harness.sentMessages.at(-1).reply_markup.inline_keyboard[1][0].callback_data,
      "scan_batch_start"
    );
  });
});

test("single part scan preview can be edited and saved without source device", async () => {
  const harness = createTelegramFlowHarness({
    partRecognitionResponse:
      '{"part_name":"Sterownik silnika","part_number":"DRV-7788","description":"Układ sterownika silnika.","category":"driver","parameters":{"Voltage":"12V"},"confidence":0.91}',
  });
  const initialDeviceCount = harness.db.state.devices.length;

  await withMockedFetch(harness.fetchImpl, async () => {
    await harness.sendWebhook({
      callback_query: {
        id: "cb-start-part",
        from: { id: 3 },
        message: { message_id: 21, chat: { id: 4, type: "private" } },
        data: "scan_part_start",
      },
    });

    await harness.sendWebhook({
      update_id: 2,
      message: {
        message_id: 22,
        from: { id: 3, username: "tester" },
        chat: { id: 4, type: "private" },
        photo: [{ file_id: "part-photo-1" }],
      },
    });
    assert.match(harness.sentMessages.at(-1).text, /Rozpoznałem część ze zdjęcia/);
    assert.equal(harness.sentMessages.at(-1).reply_markup.inline_keyboard[0][0].callback_data, "scan_part_add");

    await harness.sendWebhook({
      callback_query: {
        id: "cb-edit-part",
        from: { id: 3 },
        message: { message_id: 23, chat: { id: 4, type: "private" } },
        data: "scan_part_edit",
      },
    });

    await harness.sendWebhook({
      update_id: 3,
      message: {
        message_id: 24,
        from: { id: 3, username: "tester" },
        chat: { id: 4, type: "private" },
        text: "Driver kontrolera | DRV-7788-REV2",
      },
    });
    assert.match(harness.sentMessages.at(-1).text, /Zaktualizowałem podgląd części/);
    assert.match(harness.sentMessages.at(-1).text, /DRV-7788-REV2/);

    await harness.sendWebhook({
      callback_query: {
        id: "cb-add-part",
        from: { id: 3 },
        message: { message_id: 25, chat: { id: 4, type: "private" } },
        data: "scan_part_add",
      },
    });
    assert.match(harness.sentMessages.at(-1).text, /Podaj model elektrośmiecia źródłowego/);

    await harness.sendWebhook({
      callback_query: {
        id: "cb-no-model",
        from: { id: 3 },
        message: { message_id: 26, chat: { id: 4, type: "private" } },
        data: "scan_part_no_model",
      },
    });

    assert.match(harness.sentMessages.at(-1).text, /bez urządzenia źródłowego/);
    assert.match(harness.sentMessages.at(-1).text, /Analiza Datasheet/);
    assert.equal(harness.db.state.devices.length, initialDeviceCount);
    assert.equal(
      harness.db.state.parts.some((part) => part.part_number === "DRV-7788-REV2"),
      true
    );
  });
});

test("existing scanned part can open part question flow", async () => {
  const harness = createTelegramFlowHarness({
    partRecognitionResponse:
      '{"part_name":"ATmega328P","part_number":"ATMEGA328P-PU","description":"8-bit AVR microcontroller.","category":"mcu","parameters":{"Flash":"32KB"},"confidence":0.94}',
    partQaResponse:
      "To mikrokontroler AVR 8-bit. W bazie jest też donor Arduino Compatible Uno Clone.",
  });

  await withMockedFetch(harness.fetchImpl, async () => {
    await harness.sendWebhook({
      callback_query: {
        id: "cb-start-existing",
        from: { id: 3 },
        message: { message_id: 30, chat: { id: 4, type: "private" } },
        data: "scan_part_start",
      },
    });

    await harness.sendWebhook({
      update_id: 4,
      message: {
        message_id: 31,
        from: { id: 3, username: "tester" },
        chat: { id: 4, type: "private" },
        photo: [{ file_id: "part-photo-2" }],
      },
    });
    assert.match(harness.sentMessages.at(-1).text, /Ta część jest już w bazie/);
    assert.equal(
      harness.sentMessages.at(-1).reply_markup.inline_keyboard[0][0].callback_data,
      "part_question_start:1"
    );

    await harness.sendWebhook({
      callback_query: {
        id: "cb-part-question",
        from: { id: 3 },
        message: { message_id: 32, chat: { id: 4, type: "private" } },
        data: "part_question_start:1",
      },
    });

    await harness.sendWebhook({
      update_id: 5,
      message: {
        message_id: 33,
        from: { id: 3, username: "tester" },
        chat: { id: 4, type: "private" },
        text: "Do czego służy ta część?",
      },
    });
    assert.match(harness.sentMessages.at(-1).text, /donor Arduino Compatible Uno Clone/);
  });
});

test("batch flow accepts manual model and manual part entry, then finishes", async () => {
  const harness = createTelegramFlowHarness();

  await withMockedFetch(harness.fetchImpl, async () => {
    await harness.sendWebhook({
      callback_query: {
        id: "cb-batch-start",
        from: { id: 3 },
        message: { message_id: 40, chat: { id: 4, type: "private" } },
        data: "scan_batch_start",
      },
    });
    assert.match(harness.sentMessages.at(-1).text, /Ten tryb służy do przypisywania wielu części/);

    await harness.sendWebhook({
      callback_query: {
        id: "cb-batch-manual",
        from: { id: 3 },
        message: { message_id: 41, chat: { id: 4, type: "private" } },
        data: "scan_batch_enter_model",
      },
    });

    await harness.sendWebhook({
      update_id: 6,
      message: {
        message_id: 42,
        from: { id: 3, username: "tester" },
        chat: { id: 4, type: "private" },
        text: "Lenovo ThinkPad T480",
      },
    });
    assert.match(harness.sentMessages.at(-1).text, /Tryb dodawania wielu części aktywny/);

    await harness.sendWebhook({
      update_id: 7,
      message: {
        message_id: 43,
        from: { id: 3, username: "tester" },
        chat: { id: 4, type: "private" },
        text: "Płytka sterująca | CTRL-900",
      },
    });
    assert.match(harness.sentMessages.at(-1).text, /Zapisano część dla modelu \*Lenovo ThinkPad T480\*/);
    assert.equal(
      harness.db.state.deviceParts.some((row) => {
        const device = harness.db.state.devices.find((item) => item.id === row.device_id);
        const part = harness.db.state.parts.find((item) => item.id === row.master_part_id);
        return device?.model === "Lenovo ThinkPad T480" && part?.part_number === "CTRL-900";
      }),
      true
    );

    await harness.sendWebhook({
      callback_query: {
        id: "cb-batch-finish",
        from: { id: 3 },
        message: { message_id: 44, chat: { id: 4, type: "private" } },
        data: "scan_batch_finish",
      },
    });
    assert.match(harness.sentMessages.at(-1).text, /Zakończyłem tryb dodawania wielu części/);
  });
});

test("batch flow can preview model from photo before activation", async () => {
  const harness = createTelegramFlowHarness({
    deviceRecognitionResponse:
      '{"brand":"Lenovo","model":"ThinkPad T480","confidence":0.88}',
  });

  await withMockedFetch(harness.fetchImpl, async () => {
    await harness.sendWebhook({
      callback_query: {
        id: "cb-batch-start-photo",
        from: { id: 3 },
        message: { message_id: 45, chat: { id: 4, type: "private" } },
        data: "scan_batch_start",
      },
    });
    await harness.sendWebhook({
      callback_query: {
        id: "cb-batch-photo-choice",
        from: { id: 3 },
        message: { message_id: 46, chat: { id: 4, type: "private" } },
        data: "scan_batch_photo_model",
      },
    });

    await harness.sendWebhook({
      update_id: 8,
      message: {
        message_id: 47,
        from: { id: 3, username: "tester" },
        chat: { id: 4, type: "private" },
        photo: [{ file_id: "model-photo-1" }],
      },
    });
    assert.match(harness.sentMessages.at(-1).text, /Rozpoznałem model elektrośmiecia ze zdjęcia/);
    assert.equal(
      harness.sentMessages.at(-1).reply_markup.inline_keyboard[0][0].callback_data,
      "scan_batch_model_use"
    );
  });
});

test("handleFinalDatasheetRagFinal falls back when PDF multimodal provider returns internal error", async () => {
  const db = createScanFlowDbMock();
  const env = {
    DB: db,
    TELEGRAM_BOT_TOKEN: "telegram-token",
    TELEGRAM_AI_PRIMARY_PROVIDER: "google",
    TELEGRAM_AI_FALLBACK_PROVIDER: "nvidia",
    TELEGRAM_AI_GOOGLE_MODEL: "gemini-3.1-flash-lite-preview",
    TELEGRAM_AI_NVIDIA_MODEL: "google/gemma-4-31b-it",
    TELEGRAM_AI_TIMEOUT_MS: "20000",
    GEMINI_API_KEY: "google-key",
  };

  await withMockedFetch(async (url, init = {}) => {
    const urlString = String(url);
    if (urlString.includes("api.telegram.org/bottelegram-token/sendMessage")) {
      return jsonResponse({ ok: true });
    }
    if (urlString.includes("api.telegram.org/bottelegram-token/getFile")) {
      return jsonResponse({ ok: true, result: { file_path: "datasheet.pdf" } });
    }
    if (urlString.includes("api.telegram.org/file/bottelegram-token/datasheet.pdf")) {
      return new Response(Uint8Array.from([37, 80, 68, 70, 45, 49, 46, 55]), { status: 200 });
    }
    if (urlString.includes("generativelanguage.googleapis.com")) {
      const body = JSON.parse(init.body);
      const hasPdfMedia = JSON.stringify(body).includes("\"application/pdf\"");
      if (hasPdfMedia) {
        return jsonResponse({ error: { message: "Internal error encountered." } }, 500);
      }
      return jsonResponse({
        candidates: [
          {
            content: {
              parts: [
                {
                  text: "TDA7294 to wzmacniacz audio mocy. Odpowiadam z lokalnej bazy i fallbacku tekstowego, bo analiza PDF chwilowo nie zadziałała.",
                },
              ],
            },
          },
        ],
      });
    }
    throw new Error(`Unexpected URL: ${urlString}`);
  }, async () => {
    const session = {
      chat_id: "4",
      user_id: "3",
      active_device_name: JSON.stringify({
        version: 2,
        part_number: "TDA7294",
        master_part_id: 1,
        donor_device_model: "Wzmacniacz testowy",
        donor_device_id: null,
        pdf_url: "",
        pdf_file_id: "telegram-pdf-1",
        db_hit: true,
        source: "uploaded_pdf",
        file_name: "tda7294.pdf",
        scan_summary: "",
      }),
    };

    const reply = await handleFinalDatasheetRagFinal(
      env,
      { chat_id: "4", user_id: "3", message_id: "99" },
      session,
      "Jakie to ma zastosowanie?"
    );

    assert.match(reply.reply_text, /Analiza zakończona/);
    assert.doesNotMatch(reply.reply_text, /DS-AI-CHAIN-UNAVAILABLE/);
    assert.match(reply.reply_text, /wzmacniacz audio mocy/i);
  });
});

test("recycled_add_parts callback reuses new batch flow", async () => {
  const harness = createTelegramFlowHarness();

  await withMockedFetch(harness.fetchImpl, async () => {
    await harness.sendWebhook({
      callback_query: {
        id: "cb-recycled-batch",
        from: { id: 3 },
        message: { message_id: 50, chat: { id: 4, type: "private" } },
        data: "recycled_add_parts:20",
      },
    });

    assert.match(harness.sentMessages.at(-1).text, /Tryb dodawania wielu części aktywny/);
    assert.match(harness.sentMessages.at(-1).text, /ThinkPad T480/);
    assert.equal(
      harness.sentMessages.at(-1).reply_markup.inline_keyboard[0][0].callback_data,
      "scan_batch_change_model"
    );
  });
});
