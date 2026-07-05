#!/data/data/com.termux/files/usr/bin/bash
# nsip-client.sh — klient API Straży dla węzłów edge (smartfon proot)
# Użycie:
#   nsip-client register [--env prod] [--name "stary-s3-node1"]
#   nsip-client observe  '{"kind":"observation","metric":"temp","value":24.1,"unit":"C"}'
#   nsip-client event     '{"kind":"event","type":"pump_on","details":"gpio 12=1 by maintainer"}'
#   nsip-client rotate-token
#
# Konfiguracja: /etc/straz-edge/provider.env (chmod 0600)
#   NSIP_API_URL — endpoint API (domyślnie https://straz-przyszlosci.workers.dev)
#   NSIP_PROVIDER_ID — z rejestracji
#   NSIP_WRITE_TOKEN — z rejestracji (lub po rotacji)
#   NSIP_PROVIDER_ENV — environment slug (domyślnie prod)
#   NSIP_POND_ID — identyfikator zasobu/steku (obowiązkowe dla observations/events)

set -u

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROVIDER_ENV="${HOME:-/root}/.config/straz-edge/provider.env"
SPOOL_DIR=""
SPOOL_MAX_RETRIES=5

PRINT_JSON=0

load_env() {
  if [ ! -f "$PROVIDER_ENV" ]; then
    echo '{"error":"provider.env nie istnieje. Uruchom: nsip-client register"}'
    exit 1
  fi
  # Jawne dozowanie lista dostępnych zmiennych — ogranicza ataki injection
  # przez złośliwy provider.env.
  local safe_keys="NSIP_API_URL NSIP_PROVIDER_ID NSIP_WRITE_TOKEN NSIP_PROVIDER_ENV NSIP_POND_ID NSIP_SPOOL_DIR NSIP_SPOOL_MAX_RETRIES"
  while IFS= read -r line; do
    key="${line%%=*}"
    val="${line#*=}"
    # Obetnij otaczające cudzysłowy ("..." lub '...') jeśli są obecne.
    case "$val" in
      \"*\") val="${val#\"}"; val="${val%\"}" ;;
      \'*\') val="${val#\'}"; val="${val%\'}" ;;
    esac
    case " $safe_keys " in
      *" $key "*)
        case "$key" in
          NSIP_API_URL|NSIP_PROVIDER_ID|NSIP_WRITE_TOKEN|NSIP_PROVIDER_ENV|NSIP_POND_ID|NSIP_SPOOL_DIR|NSIP_SPOOL_MAX_RETRIES)
            printf -v "$key" '%s' "$val"
            ;;
        esac
        ;;
    esac
  done < "$PROVIDER_ENV"
  : ${NSIP_API_URL?:"NSIP_API_URL not set in provider.env"}
  : ${NSIP_PROVIDER_ID?:"NSIP_PROVIDER_ID not set"}
  : ${NSIP_WRITE_TOKEN?:"NSIP_WRITE_TOKEN not set"}
  : ${NSIP_PROVIDER_ENV:="prod"}
  NSIP_POND_ID="${NSIP_POND_ID:-default-node}"
  SPOOL_DIR="${NSIP_SPOOL_DIR:-${HOME:-/root}/.cache/straz-edge/spool}"
  SPOOL_MAX_RETRIES="${NSIP_SPOOL_MAX_RETRIES:-5}"
  # Sanity: limit retries by 1..100
  if ! [ "$SPOOL_MAX_RETRIES" -ge 1 ] 2>/dev/null || ! [ "$SPOOL_MAX_RETRIES" -le 100 ] 2>/dev/null; then
    SPOOL_MAX_RETRIES=5
  fi
  # Cyberbezpieczeństwo: w środowisku prod wymagaj https:// — token w plain HTTP
  # byłby podsłuchiwany. Zezwól na http:// tylko gdy env != prod.
  if [ "$NSIP_PROVIDER_ENV" = "prod" ]; then
    case "$NSIP_API_URL" in
      https://*) ;;
      *) echo "{\"error\":\"NSIP_API_URL musi być https:// w środowisku prod (cyber: token w plain HTTP = podsłuch)\",\"url\":\"$NSIP_API_URL\"}"; exit 1 ;;
    esac
  fi
}

python_post() {
  local url=$1; local body=$2; local token=$3
  python3 - "$url" "$body" "$token" "${NSIP_PROVIDER_ENV}" <<'PY'
import sys, json, urllib.request, ssl, urllib.error
url, body_str, token, env = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
data = json.loads(body_str)
req = urllib.request.Request(url, data=json.dumps(data).encode(),
    headers={
        "Authorization": "Bearer " + token,
        "Content-Type": "application/json",
        "X-Provider-Environment": env,
    })
ctx = ssl.create_default_context()
try:
    with urllib.request.urlopen(req, context=ctx) as resp:
        print(resp.read().decode())
except urllib.error.HTTPError as e:
    print(e.read().decode())
    sys.exit(1)
except Exception as e:
    print(json.dumps({"error": str(e)}))
    sys.exit(1)
PY
}

# Próba POST z rozróżnieniem błędu sieci (spool) od HTTP 4xx/5xx (błąd aplikacji).
# Wyjście: status na stderr. Zwraca: 0 SENT, 1 HTTP_ERROR (retry niepotrzebny), 2 NET_ERROR (spool).
try_post() {
  local url=$1; local body=$2
  local out rc
  out=$(python3 - "$url" "$body" "${NSIP_WRITE_TOKEN}" "${NSIP_PROVIDER_ENV}" <<'PY'
import sys, json, urllib.request, ssl, urllib.error
url, body_str, token, env = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
data = json.loads(body_str)
req = urllib.request.Request(url, data=json.dumps(data).encode(),
    headers={
        "Authorization": "Bearer " + token,
        "Content-Type": "application/json",
        "X-Provider-Environment": env,
    })
ctx = ssl.create_default_context()
try:
    with urllib.request.urlopen(req, context=ctx) as resp:
        sys.stderr.write("SENT")
        sys.exit(0)
except urllib.error.HTTPError as e:
    sys.stderr.write("HTTPERR:%d" % e.code)
    sys.exit(1)
except Exception as e:
    sys.stderr.write("NETERR")
    sys.exit(2)
PY
)
  rc=$?
  return $rc
}

# Wysyłaj payload do endpointu; przy błędzie sieci spooluj na dysk i nie rzuć.
# Zwraca 0 gdy wysłano (lub spoolowano), 1 gdy błąd HTTP (4xx/5xx).
post_or_spool() {
  local endpoint=$1; local kind=$2; local body=$3
  local rc
  local url="${NSIP_API_URL}${endpoint}"
  try_post "$url" "$body" 2>/tmp/nsip-try-$$.err; rc=$?
  if [ "$rc" -eq 0 ]; then
    rm -f /tmp/nsip-try-$$.err 2>/dev/null || true
    return 0
  fi
  local status; status=$(cat /tmp/nsip-try-$$.err 2>/dev/null); rm -f /tmp/nsip-try-$$.err 2>/dev/null || true
  if [ "$rc" -eq 2 ]; then
    : # NETERR — spooluj poniżej
  else
    # HTTPERR — błąd aplikacji; retry nie ma sensu (np. 429 — rate limited).
    echo "{\"ok\":false,\"spooled\":false,\"reason\":\"http_error\",\"status\":\"${status}\",\"kind\":\"${kind}\"}"
    return 1
  fi
  # Sieć zawiodła (timeout/DNS/TLS) — spooluj do offline bufora.
  mkdir -p "$SPOOL_DIR" 2>/dev/null || true
  chmod 0700 "$SPOOL_DIR" 2>/dev/null || true
  local ts; ts=$(date +%s)
  local fname="${SPOOL_DIR}/${ts}_${kind}_$$.jsonl"
  printf '%s\t%s\t%s\t%s\n' "$kind" "${NSIP_PROVIDER_ID:-unknown}" "$endpoint" "$body" > "$fname" 2>/dev/null || true
  chmod 0600 "$fname" 2>/dev/null || true
  echo "{\"ok\":false,\"spooled\":true,\"reason\":\"network_error\",\"file\":\"${fname}\",\"kind\":\"${kind}\"}"
  return 0
}

# Wysyłaj buforowane payloady z exponential backoff (1s, 2s, 4s, 8s, 16s max).
flush() {
  load_env
  if [ ! -d "$SPOOL_DIR" ]; then
    echo "{\"ok\":true,\"flushed\":0,\"note\":\"no spool dir\"}"
    return 0
  fi
  local flushed=0
  local skipped=0
  local dropped=0
  shopt -s nullglob
  for file in "$SPOOL_DIR"/*_*.jsonl; do
    [ -f "$file" ] || continue
    local line; line=$(head -1 "$file" 2>/dev/null) || { skipped=$((skipped+1)); continue; }
    local kind provider_id endpoint body
    kind=$(printf '%s' "$line" | cut -f1)
    provider_id=$(printf '%s' "$line" | cut -f2)
    endpoint=$(printf '%s' "$line" | cut -f3)
    body=$(printf '%s' "$line" | cut -f4-)
    local attempt=0
    local max=5
    local sent=0
    local rc
    while [ "$attempt" -lt "$max" ]; do
      attempt=$((attempt+1))
      try_post "${NSIP_API_URL}${endpoint}" "$body" 2>/dev/null; rc=$?
      if [ "$rc" -eq 0 ]; then
        rm -f "$file"
        sent=1
        flushed=$((flushed+1))
        break
      elif [ "$rc" -eq 1 ]; then
        # HTTPERR — błąd aplikacji (4xx/5xx). Zostaw plik ale nie retryuj już
        # bo to nie sieć; drop po przekroczeniu MAX.
        break
      fi
      if [ "$attempt" -lt "$max" ]; then
        # exponential backoff: 2^(attempt-1) sekund, max 16s
        local delay=$(( 2 ** (attempt - 1) ))
        [ "$delay" -gt 16 ] && delay=16
        sleep "$delay" 2>/dev/null || true
      fi
    done
    if [ "$sent" -eq 0 ]; then
      # Przekroczyliśmy retry — zachowaj plik ale oznacz, że drop przy kolejnym flushu
      local retry_count
      retry_count=$(grep -c '^' "$file" 2>/dev/null || echo 1)
      if [ "$retry_count" -ge "$SPOOL_MAX_RETRIES" ]; then
        dropped=$((dropped+1))
        rm -f "$file"
      else
        skipped=$((skipped+1))
      fi
    fi
  done
  shopt -u nullglob
  echo "{\"ok\":true,\"flushed\":${flushed},\"skipped\":${skipped},\"dropped\":${dropped},\"spool_dir\":\"${SPOOL_DIR}\"}"
}

# Heartbeat: lekki puls co N sekund — aktualizuje last_seen_at i sprawdza spool.
heartbeat() {
  local interval="${1:-60}"
  interval=$(printf '%d' "$interval" 2>/dev/null || echo 60)
  [ "$interval" -lt 5 ] && interval=5
  load_env
  echo "{\"ok\":true,\"heartbeat_started\":true,\"interval\":${interval},\"provider_id\":\"${NSIP_PROVIDER_ID}\"}"
  while true; do
    # Flush bufora offline, potem heartbeat POST
    flush >/dev/null 2>&1 || true
    python_post "${NSIP_API_URL}/v1/providers/${NSIP_PROVIDER_ID}/heartbeat" '{}' "${NSIP_WRITE_TOKEN}" >/dev/null 2>&1 || true
    sleep "$interval" 2>/dev/null || true
  done
}

# Częściowy loader dla 'register' — nie wymaga provider_id/token (jeszcze nie istnieją).
load_env_partial() {
  if [ ! -f "$PROVIDER_ENV" ]; then return 0; fi
  local safe_keys="NSIP_API_URL NSIP_PROVIDER_ENV NSIP_PROVIDER_ID NSIP_WRITE_TOKEN NSIP_POND_ID NSIP_SPOOL_DIR NSIP_SPOOL_MAX_RETRIES"
  while IFS= read -r line; do
    key="${line%%=*}"
    val="${line#*=}"
    case "$val" in
      \"*\") val="${val#\"}"; val="${val%\"}" ;;
      \'*\') val="${val#\'}"; val="${val%\'}" ;;
    esac
    case " $safe_keys " in
      *" $key "*)
        case "$key" in
          NSIP_API_URL|NSIP_PROVIDER_ID|NSIP_WRITE_TOKEN|NSIP_PROVIDER_ENV|NSIP_POND_ID|NSIP_SPOOL_DIR|NSIP_SPOOL_MAX_RETRIES)
            printf -v "$key" '%s' "$val"
            ;;
        esac
        ;;
    esac
  done < "$PROVIDER_ENV"
  : ${NSIP_API_URL:="https://straz-przyszlosci.workers.dev"}
  : ${NSIP_PROVIDER_ENV:="prod"}
  NSIP_POND_ID="${NSIP_POND_ID:-default-node}"
  SPOOL_DIR="${NSIP_SPOOL_DIR:-${HOME:-/root}/.cache/straz-edge/spool}"
  SPOOL_MAX_RETRIES="${NSIP_SPOOL_MAX_RETRIES:-5}"
  if ! [ "$SPOOL_MAX_RETRIES" -ge 1 ] 2>/dev/null || ! [ "$SPOOL_MAX_RETRIES" -le 100 ] 2>/dev/null; then
    SPOOL_MAX_RETRIES=5
  fi
}

register() {
  local name=$1
  load_env_partial
  if [ -n "${NSIP_PROVIDER_ID:-}" ] && [ -n "${NSIP_WRITE_TOKEN:-}" ]; then
    echo "{\"msg\":\"juz zarejestrowany\",\"provider_id\":\"$NSIP_PROVIDER_ID\"}"
    return 0
  fi
  local payload
  payload=$(python3 - "$name" "$(hostname)" "${NSIP_PROVIDER_ENV}" <<'PY'
import sys, json
name, hostname, env = sys.argv[1], sys.argv[2], sys.argv[3]
p = {
    "provider_id": "straz-edge:%s:%s" % (hostname, name),
    "provider_name": name,
    "description": "Straz Edge node (smartfon proot)",
    "schema_version": "v1",
    "provider_environment": env,
    "capabilities": ["observations", "events", "gpio-control"],
}
print(json.dumps(p))
PY
)
  local resp
  resp=$(python_post "${NSIP_API_URL}/v1/providers/register" "$payload" "" 2>/dev/null || echo '{"error":"register failed"}')
  echo "$resp" | tee /tmp/nsip-register-response.json 2>/dev/null || echo "$resp"
  local token pid
  token=$(printf '%s' "$resp" | python3 -c "import sys,json; print(json.load(sys.stdin).get('write_token',''))" 2>/dev/null || true)
  pid=$(printf '%s' "$resp" | python3 -c "import sys,json; print(json.load(sys.stdin).get('provider_id',''))" 2>/dev/null || true)
  if [ -n "$token" ] && [ -n "$pid" ]; then
    mkdir -p "$(dirname "$PROVIDER_ENV")"
    # Zapis z cytatowaniem wartości przez python (bezpieczne cyfrowe quote).
    python3 - "$PROVIDER_ENV" "$NSIP_API_URL" "$pid" "$token" "$NSIP_PROVIDER_ENV" "${NSIP_POND_ID:-default-node}" <<'PY'
import sys
path, url, pid, token, env, pond = sys.argv[1:7]
with open(path, "w") as fh:
    fh.write("# Straż Edge provider config (chmod 0600)\n")
    fh.write('NSIP_API_URL="%s"\n' % url)
    fh.write('NSIP_PROVIDER_ID="%s"\n' % pid)
    fh.write('NSIP_WRITE_TOKEN="%s"\n' % token)
    fh.write('NSIP_PROVIDER_ENV="%s"\n' % env)
    fh.write('NSIP_POND_ID="%s"\n' % pond)
PY
    chmod 0600 "$PROVIDER_ENV"
    echo "{\"ok\":true,\"provider_id\":\"$pid\",\"token_saved\":true}"
  else
    echo "{\"error\":\"parsing write_token failed\"}"
    return 1
  fi
}

observe() {
  local payload=$1
  load_env
  local full
  full=$(python3 - "$payload" "${NSIP_PROVIDER_ID}" "${NSIP_PROVIDER_ENV}" "${NSIP_POND_ID}" <<'PY'
import sys, json
payload_str, provider_id, env, pond = sys.argv[1:5]
if payload_str:
    p = json.loads(payload_str)
else:
    p = {"kind": "observation", "metric": "uptime", "value": 1}
p["provider"] = {"provider_id": provider_id, "provider_environment": env}
p["pond"] = {"pond_id": pond}
print(json.dumps(p))
PY
)
  post_or_spool "/v1/observations" "observe" "$full"
}

event() {
  local payload=$1
  load_env
  local full
  full=$(python3 - "$payload" "${NSIP_PROVIDER_ID}" "${NSIP_PROVIDER_ENV}" "${NSIP_POND_ID}" <<'PY'
import sys, json
payload_str, provider_id, env, pond = sys.argv[1:5]
if payload_str:
    p = json.loads(payload_str)
else:
    p = {"kind": "telemetry", "event_type": "unknown"}
p["provider"] = {"provider_id": provider_id, "provider_environment": env}
p["pond"] = {"pond_id": pond}
print(json.dumps(p))
PY
)
  post_or_spool "/v1/events" "event" "$full"
}

rotate() {
  load_env
  local resp
  resp=$(python_post "${NSIP_API_URL}/v1/providers/${NSIP_PROVIDER_ID}/tokens/rotate" '{}' "${NSIP_WRITE_TOKEN}")
  local token
  token=$(printf '%s' "$resp" | python3 -c "import sys,json; print(json.load(sys.stdin).get('write_token',''))" 2>/dev/null || true)
  if [ -n "$token" ]; then
    # Bezpieczny update przez python (zamiast sed — token może mieć znaki specjalne).
    python3 - "$PROVIDER_ENV" "$token" <<'PY'
import sys, re
path, token = sys.argv[1], sys.argv[2]
with open(path, "r") as fh:
    content = fh.read()
new = re.sub(r'^NSIP_WRITE_TOKEN=.*$', 'NSIP_WRITE_TOKEN="%s"' % token, content, count=1, flags=re.M)
with open(path, "w") as fh:
    fh.write(new)
PY
    chmod 0600 "$PROVIDER_ENV"
    echo "{\"ok\":true,\"token_rotated\":true}"
  else
    printf '%s\n' "$resp"
    return 1
  fi
}

status() {
  load_env
  python3 - "${NSIP_API_URL}/v1/providers/${NSIP_PROVIDER_ID}" "${NSIP_WRITE_TOKEN}" "${NSIP_PROVIDER_ENV}" <<'PY'
import sys, json, urllib.request, ssl, urllib.error
url, token, env = sys.argv[1], sys.argv[2], sys.argv[3]
req = urllib.request.Request(url, method="GET",
    headers={
        "Authorization": "Bearer " + token,
        "X-Provider-Environment": env,
    })
ctx = ssl.create_default_context()
try:
    with urllib.request.urlopen(req, context=ctx) as resp:
        print(resp.read().decode())
except urllib.error.HTTPError as e:
    print(e.read().decode())
    sys.exit(1)
except Exception as e:
    print(json.dumps({"error": str(e)}))
    sys.exit(1)
PY
}

help() {
  cat <<HELP
nsip-client — klient API Straży dla węzłów edge

  nsip-client register [--env prod] [--name "węzeł-nazwa"]     zarejestruj ten smartfon jako provider
  nsip-client observe  '<json>'                                wyślij obserwację (metric, value, unit)
  nsip-client event     '<json>'                               wyślij event (kind, event_type, details)
  nsip-client heartbeat [interval=60]                         pętla: flush spoolu + POST heartbeat co N s (min 5)
  nsip-client flush                                             ponów wysyłkę buforowanych payloadów (offline retry)
  nsip-client rotate-token                                     rotuj write_token bez zmiany provider_id
  nsip-client status                                           sprawdź status providera

Offline bufor: gdy sieć zawiedzie (timeout/DNS/TLS), payloady z observe/event
trafiają do katalogu ${SPOOL_DIR} (format: <ts>_<kind>_<pid>.jsonl).
'nsip-client flush' ponawia z exponential backoff (1s,2s,4s,8s,16s).
Pliki przekraczające SPOOL_MAX_RETRIES=${SPOOL_MAX_RETRIES} prób są dropowane.

Konfiguracja: $PROVIDER_ENV (0600, generowany przez 'nsip-client register')
HELP
}

main() {
  local cmd=${1:-help}
  shift 2>/dev/null || true
  case "$cmd" in
    register)
      local name="${1:-$(hostname)}"
      register "$name"
      ;;
    observe)
      observe "${1:-}"
      ;;
    event)
      event "${1:-}"
      ;;
    heartbeat)
      heartbeat "${1:-60}"
      ;;
    flush)
      flush
      ;;
    rotate-token|rotate)
      rotate
      ;;
    status)
      status
      ;;
    help|--help|-h)
      help
      ;;
    *)
      echo '{"error":"unknown command. See: nsip-client help"}'
      exit 1
      ;;
  esac
}

main "$@"