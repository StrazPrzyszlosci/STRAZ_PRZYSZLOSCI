/**
 * T39 — onboarding grow-agenta (T28) prosto z bota.
 *
 * `!grow-agent setup <cell_id>` / `/grow-agent setup <cell_id>` zwraca gotowy
 * przepis PL. BEZPIECZEŃSTWO: token providera NIGDY nie jest drukowany w
 * reply — użytkownik dostaje placeholder i odsyłkę do flow rejestracji
 * (/v1/providers/register), który zwraca token raz przy tworzeniu.
 */

const CELL_ID_RE = /^[a-z0-9][a-z0-9_-]{2,80}$/;

function trimText(value) {
  return String(value || "").trim();
}

export function parseGrowAgentSetupCommand(text) {
  const match = trimText(text).match(/^!(?:grow-agent|grow_agent)\s+setup\s+([^\s]+)$/i);
  if (!match) return null;
  return { cell_id: match[1].toLowerCase() };
}

export function validateGrowCellId(cellId) {
  const value = trimText(cellId);
  if (!CELL_ID_RE.test(value)) {
    throw new Error("Nieprawidłowy identyfikator komórki (3-80 znaków: a-z, 0-9, '_', '-').");
  }
  return value;
}

export function buildGrowAgentSetupReply(cellId) {
  let normalized;
  try {
    normalized = validateGrowCellId(cellId);
  } catch (err) {
    return `Blad: ${err.message}`;
  }
  return [
    `🌱 **Setup grow-agenta dla \`${normalized}\`** (advisory-only)`,
    "",
    "**1) Rejestracja providera** (jeśli komórka nie istnieje):",
    "POST /v1/providers/register — odpowiedź zawiera write_token POKAZANY RAZ; nie udostępniaj go.",
    "",
    "**2) Na urządzeniu edge (Termux/proot):**",
    "```bash",
    `export AGRI_PROVIDER_ID="${normalized}"`,
    'export AGRI_PROVIDER_TOKEN="<TOKEN_Z_REJESTRACJI>"',
    "python3 agri_grow_agent/agent.py --api-base https://<worker>.workers.dev",
    "```",
    "",
    "**Pętla co 5 minut:**",
    "```bash",
    "python3 agri_grow_agent/agent.py --interval-seconds 300 --cycles 12",
    "```",
    "",
    "**Kill switch (wstrzymuje polla):**",
    "```bash",
    "touch ~/agri_kill_switch   # usunięcie pliku wznowi pracę",
    "```",
    "",
    "Agent tylko WYŚWIETLA zdarzenia ([ALARM]/[SUGESTIA]) — żadnych pomp/dozowników.",
    "Token trzymaj wyłącznie w env; agent nigdy go nie loguje ani nie zapisuje.",
  ].join("\n");
}

export async function handleGrowAgentCommand(message) {
  const parsed = parseGrowAgentSetupCommand(message?.text || "");
  if (!parsed) {
    return { reply_text: "Uzycie: `!grow-agent setup <cell_id>`" };
  }
  return { reply_text: buildGrowAgentSetupReply(parsed.cell_id) };
}
