from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests

from src.config import AgentConfig, AppConfig
from src.gateway.calendar_tool import CalendarTool
from src.gateway.memory import MemoryState, append_turn, load_memory, save_memory, trim_turns, turn_count
from src.llm.agent import AgentResponder
from src.messenger import TelegramMessenger


@dataclass(slots=True)
class UpdateState:
    offset: int | None = None


class TelegramGateway:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.agent = AgentResponder(
            api_key=config.llm.api_key,
            model=config.llm.model,
            system_prompt=config.agent.system_prompt,
            max_reply_words=config.agent.max_reply_words,
            reply_temperature=config.agent.reply_temperature,
        )
        self.messenger = TelegramMessenger(
            bot_token=config.messenger.telegram_bot_token,
            chat_id=config.messenger.telegram_chat_id,
        )
        self.calendar_tool = CalendarTool(
            ical_urls=config.calendar.ical_urls,
            timezone=config.schedule.timezone,
            api_key=config.llm.api_key,
            model=config.llm.model,
            max_days=config.agent.calendar_max_days,
            cache_ttl_s=config.agent.calendar_cache_ttl_s,
        )
        self.memory_path = Path(config.agent.memory_path)
        self.memory = load_memory(self.memory_path)
        self.update_state = UpdateState()

    def run(self) -> None:
        if not self.config.agent.enabled:
            print("Agent gateway disabled in config.")
            return
        self._initialize_offset()
        while True:
            started = time.time()
            try:
                self._poll_once()
            except Exception as exc:
                print(f"Gateway error: {exc}")
            elapsed = time.time() - started
            sleep_for = max(0.0, self.config.agent.poll_interval_s - elapsed)
            time.sleep(sleep_for)

    def _initialize_offset(self) -> None:
        updates = self._get_updates(limit=100, timeout=0)
        if updates:
            last_id = updates[-1].get("update_id")
            if isinstance(last_id, int):
                self.update_state.offset = last_id + 1
            print(f"Skipping {len(updates)} existing updates at startup.")
        else:
            print("No existing updates at startup.")

    def _poll_once(self) -> None:
        updates = self._get_updates(
            limit=10,
            timeout=self.config.agent.poll_timeout_s,
        )
        for update in updates:
            update_id = update.get("update_id")
            if isinstance(update_id, int):
                self.update_state.offset = update_id + 1
            message = update.get("message")
            if not isinstance(message, dict):
                continue
            if message.get("text") is None:
                continue
            sender = message.get("from") or {}
            if isinstance(sender, dict) and sender.get("is_bot"):
                continue
            chat = message.get("chat") or {}
            chat_id = str(chat.get("id", ""))
            if chat_id != self.messenger.chat_id:
                continue
            text = str(message.get("text", "")).strip()
            if not text:
                continue
            self._handle_message(text)

    def _get_updates(self, limit: int, timeout: int) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"limit": limit, "timeout": timeout}
        if self.update_state.offset is not None:
            params["offset"] = self.update_state.offset
        url = f"https://api.telegram.org/bot{self.messenger.bot_token}/getUpdates"
        response = requests.get(url, params=params, timeout=timeout + 5)
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
        result = payload.get("result", [])
        return result if isinstance(result, list) else []

    def _handle_message(self, text: str) -> None:
        calendar_context = self.calendar_tool.get_context(text)
        response_text = self.agent.respond(
            user_text=text,
            memory=self.memory,
            calendar_context=calendar_context,
        )
        self.messenger.send(response_text)
        append_turn(self.memory, text, response_text)
        trim_turns(self.memory, max_turns=self.config.agent.memory_max_turns)
        if _should_update_synopsis(self.memory, self.config.agent):
            self.memory.synopsis = self.agent.summarize_memory(self.memory)
        save_memory(self.memory_path, self.memory)


def _should_update_synopsis(memory: MemoryState, config: AgentConfig) -> bool:
    if config.synopsis_every_n_turns <= 0:
        return False
    return turn_count(memory) % config.synopsis_every_n_turns == 0
