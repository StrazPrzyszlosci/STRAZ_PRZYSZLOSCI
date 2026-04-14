
import { moderateIssueCandidate } from '../cloudflare/src/telegram_ai.js';

const env = {
    TELEGRAM_AI_ENABLED: "true",
    TELEGRAM_AI_GOOGLE_MODEL: "gemma-3-27b-it",
    TELEGRAM_AI_TIMEOUT_MS: "20000",
    TELEGRAM_AI_MAX_OUTPUT_TOKENS: "1200",
    TELEGRAM_AI_TEMPERATURE: "0.35",
    GEMINI_API_KEY: "DUMMY", // Need real key to test
};

const classification = {
    label: "pomysł",
    kind: "idea",
    content: "integracja kodu ecoEDA oraz MCP KiCad oraz dodatkowej i automatyzacji Ai do inwentaryzacji części z popularnych elektrośmieci na bazie dostępnych w internecie schematów i tworzenia bazy danych zamienników dla ecoEDA"
};

const message = {
    chat_id: "123",
    message_id: "456",
    user_id: "789"
};

// This is just to see the prompt
console.log("Mocking moderation call...");
