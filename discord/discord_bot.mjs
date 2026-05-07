import { Client, GatewayIntentBits, Events } from "discord.js";
import http from "http";
import { sendDiscordReply } from "./discord_utils.mjs";
import {
  checkRateLimit,
  sanitizeDiscordInput,
  isAllowedMimeType,
  mapAttachmentToPayload,
} from "./discord_security.mjs";

const WORKER_URL = process.env.WORKER_URL;
const DISCORD_BOT_SECRET = process.env.DISCORD_BOT_SECRET;
const DISCORD_BOT_TOKEN = process.env.DISCORD_BOT_TOKEN;

if (!WORKER_URL || !DISCORD_BOT_SECRET || !DISCORD_BOT_TOKEN) {
  console.error("Missing required env vars: WORKER_URL, DISCORD_BOT_SECRET, DISCORD_BOT_TOKEN");
  process.exit(1);
}

const MAX_ATTACHMENT_BYTES = parseInt(process.env.DISCORD_MAX_ATTACHMENT_BYTES || "8388608", 10); // 8MB default

async function forwardToWorker(payload) {
  const resp = await fetch(`${WORKER_URL}/integrations/discord/webhook`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Discord-Bot-Secret": DISCORD_BOT_SECRET,
    },
    body: JSON.stringify(payload),
  });

  if (!resp.ok) {
    console.error(`Worker returned ${resp.status}: ${await resp.text().catch(() => "")}`);
    return null;
  }

  return await resp.json();
}

const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.MessageContent,
  ],
});

client.on(Events.ClientReady, () => {
  console.log(`Discord bot logged in as ${client.user.tag}`);
});

client.on(Events.MessageCreate, async (message) => {
  if (message.author.bot) return;

  try {
    const rateLimit = checkRateLimit(message.author.id);
    if (!rateLimit.allowed) {
      console.warn(`Rate limited user ${message.author.id}, retry after ${rateLimit.retry_after_seconds}s`);
      await message.reply({ content: `⏳ Zbyt wiele wiadomości. Spróbuj ponownie za ${rateLimit.retry_after_seconds} s.`, allowedMentions: { repliedUser: false } });
      return;
    }

    const attachments = [...message.attachments.values()];
    for (const att of attachments) {
      if (att.size > MAX_ATTACHMENT_BYTES) {
        await message.reply({ content: `📦 Załącznik ${att.name || ""} jest za duży. Maksymalny rozmiar to ${MAX_ATTACHMENT_BYTES} bajtów.`, allowedMentions: { repliedUser: false } });
        return;
      }
      if (!isAllowedMimeType(att.contentType, att.name)) {
        await message.reply({ content: `🚫 Typ pliku ${att.contentType || att.name || "nieznany"} nie jest dozwolony.`, allowedMentions: { repliedUser: false } });
        return;
      }
    }

    const payload = {
      chat_id: message.channelId,
      user_id: message.author.id,
      message_id: message.id,
      text: sanitizeDiscordInput(message.content || ""),
      username: message.author.username,
      attachments: attachments.map(mapAttachmentToPayload),
      type: "message",
    };

    const data = await forwardToWorker(payload);

    if (data?.reply_text) {
      await sendDiscordReply(message, data);
    }
  } catch (err) {
    console.error("messageCreate error:", err);
  }
});

client.on(Events.InteractionCreate, async (interaction) => {
  if (!interaction.isButton() && !interaction.isStringSelectMenu()) return;

  const customId = interaction.customId || interaction.values?.[0];

  try {
    await interaction.deferUpdate();

    const payload = {
      chat_id: interaction.channelId,
      user_id: interaction.user.id,
      message_id: interaction.message?.id || "",
      callback_data: customId,
      type: "callback",
    };

    const data = await forwardToWorker(payload);

    if (data?.reply_text) {
      if (data.reply_text.length <= 2000) {
        await interaction.editReply({
          content: data.reply_text,
          components: [],
        });
      } else {
        await interaction.followUp({
          content: data.reply_text.slice(0, 2000),
          ephemeral: true,
        });
      }
    }
  } catch (err) {
    console.error("interactionCreate error:", err);
  }
});

client.on(Events.Error, (err) => {
  console.error("Discord client error:", err);
});

process.on("SIGTERM", () => {
  console.log("Shutting down Discord bot...");
  client.destroy();
  process.exit(0);
});

process.on("SIGINT", () => {
  console.log("Shutting down Discord bot...");
  client.destroy();
  process.exit(0);
});

client.login(DISCORD_BOT_TOKEN).catch((err) => {
  console.error("Login failed:", err);
  process.exit(1);
});

const PORT = process.env.PORT || 3000;
http
  .createServer((_req, res) => {
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ status: "ok", uptime: process.uptime() }));
  })
  .listen(PORT, () => {
    console.log(`Health check HTTP server listening on port ${PORT}`);
  });