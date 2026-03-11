---
summary: "Telegram delivery for summary messages"
read_when:
  - "Changing messenger handling or logic"
---

# Messenger Package

Sends the generated summary to Telegram via the Bot API.

- `TelegramMessenger.send` posts to `sendMessage` with `disable_web_page_preview`.
- Errors on non-JSON responses, HTTP >= 400, or Telegram `ok=false`.
- Returns the Telegram `message_id` as a string.

Behavior notes

- Request timeout 15s
- No retries or message splitting
- Telegram API errors surface as `RuntimeError`

Config

- `messenger.telegram_bot_token`
- `messenger.telegram_chat_id`
