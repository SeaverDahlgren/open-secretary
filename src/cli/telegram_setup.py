from __future__ import annotations

import sys
from typing import Any

import requests

from src.cli.prompts import prompt_required


def _fetch_telegram_updates(bot_token: str, limit: int) -> list[dict[str, Any]]:
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    response = requests.get(url, params={"limit": limit}, timeout=15)
    try:
        payload = response.json()
    except ValueError as exc:
        raise RuntimeError("Telegram API returned non-JSON response.") from exc
    if response.status_code >= 400:
        description = payload.get("description", "Unknown Telegram API error")
        raise RuntimeError(
            f"Telegram getUpdates failed (status {response.status_code}): {description}"
        )
    if not payload.get("ok"):
        raise RuntimeError(f"Telegram API error: {payload}")
    return payload.get("result", [])


def prompt_chat_id(bot_token: str) -> str:
    updates = _fetch_telegram_updates(bot_token, limit=50)
    chats: list[dict[str, Any]] = []
    seen_ids: set[int] = set()
    for update in updates:
        message = update.get("message") or update.get("channel_post") or update.get("edited_message")
        if not isinstance(message, dict):
            continue
        chat = message.get("chat")
        if not isinstance(chat, dict):
            continue
        chat_id = chat.get("id")
        if chat_id is None:
            continue
        chat_id = int(chat_id)
        if chat_id in seen_ids:
            continue
        seen_ids.add(chat_id)
        chats.append(chat)

    if chats:
        print("Select a Telegram chat:")
        for idx, chat in enumerate(chats):
            chat_id = chat.get("id")
            chat_type = chat.get("type", "unknown")
            title = chat.get("title") or chat.get("username") or chat.get("first_name") or ""
            label = f"{idx}: {chat_id} ({chat_type})"
            if title:
                label += f" - {title}"
            print(label)
        while True:
            choice = input("Chat index (or leave blank to enter manually): ").strip()
            if not choice:
                break
            if not choice.isdigit():
                print("Chat index must be a number.", file=sys.stderr)
                continue
            index = int(choice)
            if 0 <= index < len(chats):
                return str(chats[index].get("id"))
            print(f"Chat index must be between 0 and {len(chats) - 1}.", file=sys.stderr)
    else:
        print("No chats found. Send a message to the bot first.")

    return prompt_required("Telegram chat id")
