from __future__ import annotations

import requests


class TelegramMessenger:
    def __init__(self, bot_token: str, chat_id: str) -> None:
        self.bot_token = bot_token
        self.chat_id = str(chat_id)
        self.base_url = f"https://api.telegram.org/bot{bot_token}"

    def send(self, message: str) -> str:
        response = requests.post(
            f"{self.base_url}/sendMessage",
            json={
                "chat_id": self.chat_id,
                "text": message,
                "disable_web_page_preview": True,
            },
            timeout=15,
        )
        try:
            payload = response.json()
        except ValueError as exc:
            raise RuntimeError(
                f"Telegram API returned non-JSON response (status {response.status_code})."
            ) from exc

        if response.status_code >= 400:
            description = payload.get("description", "Unknown Telegram API error")
            raise RuntimeError(
                f"Telegram sendMessage failed (status {response.status_code}): {description}"
            )
        if not payload.get("ok"):
            raise RuntimeError(f"Telegram API error: {payload}")
        message_id = payload["result"]["message_id"]
        return str(message_id)
