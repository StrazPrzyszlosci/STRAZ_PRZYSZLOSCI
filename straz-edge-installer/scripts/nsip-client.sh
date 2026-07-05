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

PRINT_JSON=0

load_env() {
  if [ ! -f "$PROVIDER_ENV" ]; then
    echo '{"error":"provider.env nie istnieje. Uruchom: nsip-client register"}'
    exit 1
  fi
  source "$PROVIDER_ENV" 2>/dev/null || true
  : ${NSIP_API_URL?:"NSIP_API_URL not set in provider.env"}
  : ${NSIP_PROVIDER_ID?:"NSIP_PROVIDER_ID not set"}
  : ${NSIP_PROVIDER_ENV:="prod"}
  NSIP_POND_ID="${NSIP_POND_ID:-default-node}"  # można zmienić
}

python_post() {
  local url=$1; local body=$2; local token=$3
  python3 - <<PY
import sys, json, urllib.request, ssl
url, body_str, token = sys.argv[1], sys.argv[2], sys.argv[3]
data = json.loads(body_str)
req = urllib.request.Request(url, data=json.dumps(data).encode(),
    headers={
        "Authorization": "Bearer " + token,
        "Content-Type": "application/json",
        "X-Provider-Environment": "${NSIP_PROVIDER_ENV}",
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

register() {
  local name=$1
  load_env  # po rejestracji provider_id i write_token zapisać
  if [ -n "${NSIP_PROVIDER_ID:-}" ] && [ -n "${NSIP_WRITE_TOKEN:-}" ]; then
    echo "{\"msg\":\"juz zarejestrowany\",\"provider_id\":\"$NSIP_PROVIDER_ID\"}"
    return 0
  fi
  local payload
  payload=$(python3 -c "
import json
p = {
    'provider_id': 'straz-edge:$(hostname):${name}',
    'provider_name': '${name}',
    'description': 'Straz Edge node (smartfon proot)',
    'schema_version': 'v1',
    'provider_environment': '${NSIP_PROVIDER_ENV}',
    'capabilities': ['observations', 'events', 'gpio-control'],
}
print(json.dumps(p))
")
  local resp
  resp=$(python_post "${NSIP_API_URL}/v1/providers/register" "$payload" "" 2>/dev/null || echo '{"error":"register failed"}')
  echo "$resp" | tee /tmp/nsip-register-response.json
  local token pid
  token=$(echo "$resp" | python3 -c "import sys,json; print(json.load(sys.stdin).get('write_token',''))" 2>/dev/null)
  pid=$(echo "$resp" | python3 -c "import sys,json; print(json.load(sys.stdin).get('provider_id',''))" 2>/dev/null)
  if [ -n "$token" ] && [ -n "$pid" ]; then
    mkdir -p "$(dirname "$PROVIDER_ENV")"
    cat > "$PROVIDER_ENV" <<ENVEOF
# Straż Edge provider config (chmod 0600)
NSIP_API_URL="${NSIP_API_URL}"
NSIP_PROVIDER_ID="$pid"
NSIP_WRITE_TOKEN="$token"
NSIP_PROVIDER_ENV="${NSIP_PROVIDER_ENV}"
NSIP_POND_ID="${NSIP_POND_ID:-default-node}"
ENVEOF
    chmod 0600 "$PROVIDER_ENV"
    echo "{\"ok\":true,\"provider_id\":\"$pid\",\"token_saved\":true}"
  else
    echo "{\"error\":\"parsing write_token failed\",\"response\":\"$resp\"}"
    return 1
  fi
}

observe() {
  local payload=$1
  load_env
  local full
  full=$(python3 -c "
import json
p = json.loads('$payload') if '$payload' else {'kind':'observation','metric':'uptime','value':1}
p['provider'] = {'provider_id': '${NSIP_PROVIDER_ID}', 'provider_environment': '${NSIP_PROVIDER_ENV}'}
p['pond'] = {'pond_id': '${NSIP_POND_ID}'}
print(json.dumps(p))
")
  python_post "${NSIP_API_URL}/v1/observations" "$full" "${NSIP_WRITE_TOKEN}"
}

event() {
  local payload=$1
  load_env
  local full
  full=$(python3 -c "
import json
p = json.loads('$payload') if '$payload' else {'kind':'event','type':'unknown'}
p['provider'] = {'provider_id': '${NSIP_PROVIDER_ID}', 'provider_environment': '${NSIP_PROVIDER_ENV}'}
p['pond'] = {'pond_id': '${NSIP_POND_ID}'}
print(json.dumps(p))
")
  python_post "${NSIP_API_URL}/v1/events" "$full" "${NSIP_WRITE_TOKEN}"
}

rotate() {
  load_env
  local resp
  resp=$(python_post "${NSIP_API_URL}/v1/providers/${NSIP_PROVIDER_ID}/tokens/rotate" '{}' "${NSIP_WRITE_TOKEN}")
  local token
  token=$(echo "$resp" | python3 -c "import sys,json; print(json.load(sys.stdin).get('write_token',''))" 2>/dev/null)
  if [ -n "$token" ]; then
    sed -i "s/^NSIP_WRITE_TOKEN=.*/NSIP_WRITE_TOKEN=$token/" "$PROVIDER_ENV"
    echo "{\"ok\":true,\"token_rotated\":true}"
  else
    echo "$resp"
    return 1
  fi
}

status() {
  load_env
  curl -s "${NSIP_API_URL}/v1/providers/${NSIP_PROVIDER_ID}" 2>/dev/null || echo '{"error":"status request failed"}'
}

help() {
  cat <<HELP
nsip-client — klient API Straży dla węzłów edge

  nsip-client register [--env prod] [--name "węzeł-nazwa"]     zarejestruj ten smartfon jako provider
  nsip-client observe  '<json>'                                wyślij obserwację (metric, value, unit)
  nsip-client event     '<json>'                               wyślij event (type, details)
  nsip-client rotate-token                                     rotuj write_token bez zmiany provider_id
  nsip-client status                                           sprawdź status providera
  nsip-client help                                             ten ekran

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