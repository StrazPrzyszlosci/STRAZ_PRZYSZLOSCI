import { normalizeWhitespace, toIsoNow, formatDeviceName, buildDeviceCatalogReply, buildPartLookupReply, getMessageText, fetchWithTimeout } from "./base_utils.js";

export async function getDeviceById(env, deviceId) {
  const db = env.DB;
  return await db.prepare(`SELECT * FROM recycled_devices WHERE id = ?`).bind(deviceId).first();
}

export async function recordRecycledSubmission(env, payload) {
  const db = env.DB;
  if (!db) return null;
  
  let finalizedQueryText = payload.query_text || null;
  if (!finalizedQueryText && payload.matched_device_id) {
    const device = await db.prepare("SELECT brand, model FROM recycled_devices WHERE id = ?").bind(payload.matched_device_id).first();
    if (device) {
      finalizedQueryText = `${device.brand || ""} ${device.model || ""}`.trim();
    }
  }

  const res = await db.prepare(
    `
    INSERT INTO recycled_device_submissions (
      chat_id, user_id, message_id, lookup_kind, query_text, recognized_brand, recognized_model,
      matched_device_id, matched_part_name, matched_part_number, attachment_file_id, attachment_mime_type,
      provider_name, model_name, status, raw_payload_json, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `
  ).bind(
    payload.chat_id || null, payload.user_id || null, payload.message_id || null, payload.lookup_kind || "unknown",
    finalizedQueryText, payload.recognized_brand || null, payload.recognized_model || null,
    payload.matched_device_id || null, payload.matched_part_name || null, payload.matched_part_number || null,
    payload.attachment_file_id || null, payload.attachment_mime_type || null, payload.provider_name || null,
    payload.model_name || null, payload.status || "queued",
    payload.raw_payload_json ? JSON.stringify(payload.raw_payload_json) : null,
    toIsoNow()
  ).run();

  const newId = res.meta.last_row_id;

  if (newId && newId % 10 === 0) {
    const owner = env.GITHUB_REPO_OWNER;
    const repo = env.GITHUB_REPO_NAME;
    const token = env.GITHUB_TOKEN;
    if (owner && repo && token) {
      await fetchWithTimeout(`https://api.github.com/repos/${owner}/${repo}/dispatches`, {
        method: "POST",
        headers: {
          accept: "application/vnd.github+json",
          authorization: `Bearer ${token}`,
          "content-type": "application/json",
          "user-agent": "straz-przyszlosci-telegram-bridge",
          "x-github-api-version": "2022-11-28",
        },
        body: JSON.stringify({
          event_type: "trigger-backup",
          client_payload: { submission_id: newId },
        }),
      }, 5000).catch(() => {});
    }
  }

  return newId;
}

export async function getPartsForModel(env, modelName) {
  const db = env.DB;
  const queryText = normalizeWhitespace(modelName);
  if (!db || !queryText) return null;

  let device = await db.prepare(
    `
    SELECT d.*
    FROM recycled_devices d
    JOIN recycled_devices_fts f ON f.rowid = d.id
    WHERE recycled_devices_fts MATCH ?
    ORDER BY rank
    LIMIT 1
    `
  ).bind(queryText).first();

  if (!device) {
    const submissionDevice = await db.prepare(
      `SELECT DISTINCT query_text as model, recognized_brand as brand FROM recycled_device_submissions 
       WHERE (LOWER(query_text) = LOWER(?) OR LOWER(recognized_model) = LOWER(?))
       AND query_text IS NOT NULL LIMIT 1`
    ).bind(queryText, queryText).first();

    if (!submissionDevice) return null;
    device = { ...submissionDevice, id: null, description: " Urządzenie w kolejce do weryfikacji." };
  }

  const parts = await db.prepare(
    `
    SELECT
      part_name, species, value, designator, description, quantity, datasheet_url,
      kicad_symbol, kicad_footprint, ipn, category, parameters, datasheet_file_id,
      kicad_reference, stock_location
    FROM recycled_parts
    WHERE device_id = ?
    ORDER BY part_name ASC
    `
  ).bind(device.id).all();

  const submissions = await db.prepare(
    `
    SELECT
      matched_part_name as part_name, 'crowdsourced' as species, matched_part_number as value,
      NULL as designator, 'Zasób z kolejki (niezweryfikowany)' as description, 1 as quantity,
      NULL as datasheet_url, NULL as kicad_symbol, NULL as kicad_footprint,
      NULL as ipn, NULL as category, NULL as parameters, NULL as datasheet_file_id,
      NULL as kicad_reference, NULL as stock_location
    FROM recycled_device_submissions
    WHERE (
      (matched_device_id IS NOT NULL AND matched_device_id = ?)
      OR
      (matched_device_id IS NULL AND (
        LOWER(query_text) = LOWER(?) OR LOWER(recognized_model) = LOWER(?)
        OR LOWER(query_text) LIKE LOWER(?) OR LOWER(recognized_model) LIKE LOWER(?)
      ))
    )
    AND lookup_kind = 'part_media' AND matched_part_name IS NOT NULL
    `
  ).bind(device.id, device.model, device.model, `%${device.model}%`, `%${device.model}%`).all();

  const allParts = [
    ...(parts.results || []),
    ...(submissions.results || [])
  ];

  return { device, parts: allParts };
}

export async function searchPartDonors(env, queryText) {
  const db = env.DB;
  const normalizedQuery = normalizeWhitespace(queryText);
  if (!db || !normalizedQuery) return [];

  const wildcard = `%${normalizedQuery}%`;
  const result = await db.prepare(
    `
    SELECT DISTINCT
      p.*, d.id AS device_id, d.model, d.brand, d.description AS device_description, d.teardown_url
    FROM recycled_parts p
    JOIN recycled_devices d ON d.id = p.device_id
    LEFT JOIN recycled_part_aliases a ON a.part_id = p.id
    WHERE
      LOWER(p.part_name) = LOWER(?) OR LOWER(p.part_name) LIKE LOWER(?)
      OR LOWER(COALESCE(a.alias, '')) = LOWER(?) OR LOWER(COALESCE(a.alias, '')) LIKE LOWER(?)
    ORDER BY
      CASE
        WHEN LOWER(p.part_name) = LOWER(?) THEN 0
        WHEN LOWER(COALESCE(a.alias, '')) = LOWER(?) THEN 1
        ELSE 2
      END,
      p.part_name, d.brand, d.model
    LIMIT 8
    `
  ).bind(normalizedQuery, wildcard, normalizedQuery, wildcard, normalizedQuery, normalizedQuery).all();

  return (result.results || []).map((row) => ({
    ...row,
    device: {
      id: row.device_id,
      model: row.model,
      brand: row.brand,
      description: row.device_description,
      teardown_url: row.teardown_url,
    },
  }));
}

export async function handleRecycledKnowledgeLookup(env, message) {
  const queryText = normalizeWhitespace(getMessageText(message));
  if (!queryText) {
    return {
      reply_text: "Podejrzewam lookup czesci, ale nie widze tekstu do sprawdzenia.",
      provider_name: "local",
      model_name: "d1",
    };
  }

  const deviceResult = await getPartsForModel(env, queryText);
  if (deviceResult) {
    await recordRecycledSubmission(env, {
      chat_id: message?.chat_id, user_id: message?.user_id, message_id: message?.message_id,
      lookup_kind: "device_lookup", query_text: queryText, matched_device_id: deviceResult.device.id,
      status: "matched_device", raw_payload_json: { query_text: queryText },
    });
    return {
      reply_text: buildDeviceCatalogReply(deviceResult),
      provider_name: "local", model_name: "d1",
    };
  }

  const partMatches = await searchPartDonors(env, queryText);
  if (partMatches.length) {
    await recordRecycledSubmission(env, {
      chat_id: message?.chat_id, user_id: message?.user_id, message_id: message?.message_id,
      lookup_kind: "part_lookup", query_text: queryText, matched_device_id: partMatches[0].device.id,
      matched_part_name: partMatches[0].part_name, status: "matched_part",
      raw_payload_json: { query_text: queryText },
    });
    const reply = buildPartLookupReply(queryText, partMatches);
    return {
      reply_text: reply.text, reply_markup: reply.reply_markup,
      provider_name: "local", model_name: "d1",
    };
  }

  await recordRecycledSubmission(env, {
    chat_id: message?.chat_id, user_id: message?.user_id, message_id: message?.message_id,
    lookup_kind: "unknown_lookup", query_text: queryText, status: "queued",
    raw_payload_json: { query_text: queryText },
  });

  return {
    reply_text: "Nie mam jeszcze pewnego dopasowania w katalogu reuse. Wyślij model, part number albo zdjęcie etykiety / PCB, a zgłoszenie trafi do kolejki kuracji.",
    provider_name: "local", model_name: "d1",
  };
}
