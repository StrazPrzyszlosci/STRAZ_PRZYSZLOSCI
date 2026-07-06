#!/data/data/com.termux/files/usr/bin/bash
# Install or dry-run configure Hermes Agent inside Termux proot for Straż Przyszłości.
# Default mode is --dry-run so tests and operators can inspect the plan without network/secrets.

set -euo pipefail

PROOT_DISTRO="${PROOT_DISTRO:-debian}"
PROOT_USERNAME="${PROOT_USERNAME:-straz}"
HERMES_REPO_URL="${HERMES_REPO_URL:-https://github.com/NousResearch/hermes-agent.git}"
HERMES_INSTALL_DIR="${HERMES_INSTALL_DIR:-/opt/straz/hermes-agent}"
HERMES_CONFIG_DIR="${HERMES_CONFIG_DIR:-/etc/straz-hermes}"
HERMES_WORKDIR="${HERMES_WORKDIR:-/opt/straz/workspace/STRAZ_PRZYSZLOSCI}"
MODE="dry-run"
PROOT_BIN="${PROOT_BIN:-/data/data/com.termux/files/usr/bin/proot-distro}"

usage() {
  cat <<USAGE
Usage: bash scripts/install-hermes-agent-proot.sh [--install|--dry-run] [options]

Options:
  --install                 actually configure proot (network + apt + git clone)
  --dry-run                 print plan only (default, no secrets, no network)
  --distro NAME             proot-distro name (default: debian)
  --user NAME               Linux user inside proot (default: straz)
  --repo-url URL            Hermes Agent repo URL
  --install-dir PATH        install path inside proot (default: /opt/straz/hermes-agent)
  --workdir PATH            Straż repo/workspace path inside proot
  --help                    show this help
USAGE
}

while [ $# -gt 0 ]; do
  case "$1" in
    --install) MODE="install" ;;
    --dry-run) MODE="dry-run" ;;
    --distro) PROOT_DISTRO="$2"; shift ;;
    --user) PROOT_USERNAME="$2"; shift ;;
    --repo-url) HERMES_REPO_URL="$2"; shift ;;
    --install-dir) HERMES_INSTALL_DIR="$2"; shift ;;
    --workdir) HERMES_WORKDIR="$2"; shift ;;
    --help|-h) usage; exit 0 ;;
    *) echo "ERROR: unknown option: $1" >&2; usage; exit 2 ;;
  esac
  shift
done

ROOTFS="/data/data/com.termux/files/usr/var/lib/proot-distro/installed-rootfs/$PROOT_DISTRO"

print_plan() {
  cat <<PLAN
Hermes Agent proot installer plan for Straż Przyszłości
mode: $MODE
proot_distro: $PROOT_DISTRO
proot_user: $PROOT_USERNAME
repo_url: $HERMES_REPO_URL
install_dir: $HERMES_INSTALL_DIR
config_dir: $HERMES_CONFIG_DIR
workspace: $HERMES_WORKDIR

This installer configures Hermes as repo-builder/scout/handoff-builder only.
It does not store real secrets, does not auto-merge, does not push to main,
and does not enable physical actuation.

Required operator-provided secrets after install:
- GEMINI_API_KEY
- NVIDIA_API_KEY
- GITHUB_PAT limited to a fork or staging repository

Required artifacts per run:
- run_receipt.json
- model_route.json
- quota_snapshot.json
- git_diff.patch
- handoff_or_pr.md
PLAN
}

proot_exec_root() {
  "$PROOT_BIN" login "$PROOT_DISTRO" --user root -- bash -lc "$1"
}

write_proot_files_script() {
  cat <<'PROOT_SCRIPT'
set -euo pipefail
install -d -m 0755 /etc/straz-hermes /opt/straz/bin /opt/straz/workspace /opt/straz/logs
cat > /etc/straz-hermes/hermes.env.example <<'ENVEOF'
# Copy to hermes.env inside proot and fill manually. Do not commit real secrets.
GEMINI_API_KEY=__SET_BY_OPERATOR__
NVIDIA_API_KEY=__SET_BY_OPERATOR__
GITHUB_PAT=__SET_BY_OPERATOR_MINIMAL_FORK_SCOPE__
HERMES_DEFAULT_MODE=suggest-only
HERMES_ALLOWED_TASKS=repo_scout,handoff_builder,execution_pack_draft,audit_review,provider_quota_monitor
HERMES_BLOCKED_TASKS=physical_actuation,auto_merge,direct_push_main,secret_printing,unbounded_spend
HERMES_WORKDIR=/opt/straz/workspace/STRAZ_PRZYSZLOSCI
HERMES_ARTIFACT_DIR=/opt/straz/logs
ENVEOF
cat > /opt/straz/bin/straz-hermes-runner <<'RUNEOF'
#!/usr/bin/env bash
set -euo pipefail
CONFIG=${CONFIG:-/etc/straz-hermes/hermes.env}
if [ ! -f "$CONFIG" ]; then
  echo "ERROR: missing $CONFIG. Copy /etc/straz-hermes/hermes.env.example and fill secrets manually." >&2
  exit 1
fi
set -a
# shellcheck disable=SC1090
. "$CONFIG"
set +a
case ",${HERMES_BLOCKED_TASKS:-}," in
  *",physical_actuation,"*) : ;;
  *) echo "ERROR: physical_actuation must remain blocked" >&2; exit 1 ;;
esac
mkdir -p "${HERMES_ARTIFACT_DIR:-/opt/straz/logs}"
cat > "${HERMES_ARTIFACT_DIR:-/opt/straz/logs}/run_receipt.json" <<RECEIPT
{"status":"queued_review_required","mode":"${HERMES_DEFAULT_MODE:-suggest-only}","blocked_tasks":"${HERMES_BLOCKED_TASKS:-}"}
RECEIPT
cat > "${HERMES_ARTIFACT_DIR:-/opt/straz/logs}/model_route.json" <<ROUTE
{"primary":"google_ai_studio_free","fallback":"nvidia_nim_free","private":"selfhost_recovered_node"}
ROUTE
cat > "${HERMES_ARTIFACT_DIR:-/opt/straz/logs}/quota_snapshot.json" <<QUOTA
{"status":"manual_check_required","note":"Do not assume NVIDIA 40 RPM or Google project limits without live check."}
QUOTA
echo "Hermes runner prepared artifacts in ${HERMES_ARTIFACT_DIR:-/opt/straz/logs}. Start actual Hermes only after operator review."
RUNEOF
chmod 0755 /opt/straz/bin/straz-hermes-runner
PROOT_SCRIPT
}

install_inside_proot() {
  if ! command -v "$PROOT_BIN" >/dev/null 2>&1; then
    echo "ERROR: proot-distro not found. Run straz-edge-installer/install.sh first." >&2
    exit 1
  fi
  if [ ! -d "$ROOTFS" ]; then
    echo "ERROR: proot distro '$PROOT_DISTRO' not installed. Run install.sh --profile node-nsip --distro $PROOT_DISTRO first." >&2
    exit 1
  fi
  proot_exec_root "export DEBIAN_FRONTEND=noninteractive; apt-get update -y; apt-get install -y --no-install-recommends git ca-certificates python3 python3-venv python3-pip nodejs npm ripgrep jq sqlite3 openssh-client"
  proot_exec_root "$(write_proot_files_script)"
  proot_exec_root "if [ ! -d '$HERMES_INSTALL_DIR/.git' ]; then mkdir -p '$(dirname "$HERMES_INSTALL_DIR")'; git clone --depth 1 '$HERMES_REPO_URL' '$HERMES_INSTALL_DIR'; else git -C '$HERMES_INSTALL_DIR' pull --ff-only; fi"
  proot_exec_root "chown -R '$PROOT_USERNAME':'$PROOT_USERNAME' /opt/straz /etc/straz-hermes 2>/dev/null || true"
}

print_plan
if [ "$MODE" = "dry-run" ]; then
  echo "DRY_RUN_OK: no packages installed, no repository cloned, no secrets written."
  exit 0
fi
install_inside_proot
echo "INSTALL_OK: Hermes Agent scaffold installed in proot. Copy hermes.env.example to hermes.env and fill secrets manually."
