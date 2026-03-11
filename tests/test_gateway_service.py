from __future__ import annotations

from types import SimpleNamespace

import pytest

from src.config import AppConfig, CalendarConfig, LLMConfig, MessengerConfig, ScheduleConfig
from src.gateway import service as gateway_service
from src.gateway.memory import MemoryState


class DummyResponder:
    def __init__(self) -> None:
        self.responses: list[str] = []

    def respond(self, user_text: str, memory: MemoryState) -> str:
        self.responses.append(user_text)
        return f"Echo: {user_text}"

    def summarize_memory(self, memory: MemoryState) -> str:
        return "synopsis"


class DummyMessenger:
    def __init__(self, chat_id: str = "12345") -> None:
        self.sent: list[str] = []
        self.chat_id = chat_id

    def send(self, message: str) -> str:
        self.sent.append(message)
        return "MSG1"


def _config() -> AppConfig:
    return AppConfig(
        schedule=ScheduleConfig(time="08:15", days=["mon"], timezone="UTC"),
        calendar=CalendarConfig(ical_urls=["https://example.com/a.ics"]),
        llm=LLMConfig(model="gemini-2.0-flash", api_key="k"),
        messenger=MessengerConfig(telegram_bot_token="token", telegram_chat_id="12345"),
    )


def test_gateway_skips_existing_updates_on_startup(monkeypatch):
    cfg = _config()
    gateway = gateway_service.TelegramGateway(cfg)
    gateway.agent = DummyResponder()
    gateway.messenger = DummyMessenger()

    updates = [
        {"update_id": 10, "message": {"text": "old", "chat": {"id": "12345"}}},
        {"update_id": 12, "message": {"text": "old2", "chat": {"id": "12345"}}},
    ]

    def fake_get_updates(limit: int, timeout: int):
        return updates

    monkeypatch.setattr(gateway, "_get_updates", fake_get_updates)

    gateway._initialize_offset()

    assert gateway.update_state.offset == 13


def test_gateway_filters_messages(monkeypatch):
    cfg = _config()
    gateway = gateway_service.TelegramGateway(cfg)
    gateway.agent = DummyResponder()
    gateway.messenger = DummyMessenger()

    updates = [
        {"update_id": 1, "message": {"text": "hi", "chat": {"id": "999"}}},
        {"update_id": 2, "message": {"text": None, "chat": {"id": "12345"}}},
        {"update_id": 3, "message": {"text": "bot", "from": {"is_bot": True}, "chat": {"id": "12345"}}},
        {"update_id": 4, "message": {"text": "ok", "chat": {"id": "12345"}}},
    ]

    def fake_get_updates(limit: int, timeout: int):
        return updates

    monkeypatch.setattr(gateway, "_get_updates", fake_get_updates)

    gateway._poll_once()

    assert gateway.agent.responses == ["ok"]
    assert gateway.messenger.sent == ["Echo: ok"]
    assert gateway.update_state.offset == 5


def test_gateway_updates_synopsis_on_interval(monkeypatch, tmp_path):
    cfg = _config()
    cfg.agent.memory_path = str(tmp_path / "memory.md")
    cfg.agent.synopsis_every_n_turns = 2
    gateway = gateway_service.TelegramGateway(cfg)
    gateway.agent = DummyResponder()
    gateway.messenger = DummyMessenger()

    updates = [
        {"update_id": 1, "message": {"text": "first", "chat": {"id": "12345"}}},
        {"update_id": 2, "message": {"text": "second", "chat": {"id": "12345"}}},
    ]

    def fake_get_updates(limit: int, timeout: int):
        return updates

    monkeypatch.setattr(gateway, "_get_updates", fake_get_updates)

    gateway._poll_once()

    assert gateway.memory.synopsis == "synopsis"


def test_gateway_get_updates_errors(monkeypatch):
    cfg = _config()
    gateway = gateway_service.TelegramGateway(cfg)

    def fake_get(*args, **kwargs):
        return SimpleNamespace(
            status_code=500,
            json=lambda: {"ok": False, "description": "bad"},
        )

    monkeypatch.setattr(gateway_service.requests, "get", fake_get)

    with pytest.raises(RuntimeError, match="getUpdates failed"):
        gateway._get_updates(limit=1, timeout=0)
