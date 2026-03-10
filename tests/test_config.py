from __future__ import annotations

import json

import pytest

from src.config import load_config


def test_load_config_uses_env_gemini_key(tmp_path, monkeypatch):
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text(
        json.dumps(
            {
                "schedule": {"time": "09:30", "days": ["mon", "wed"], "timezone": "UTC"},
                "calendar": {"ical_url": "https://example.com/a.ics"},
                "llm": {"model": "gemini-2.0-flash", "api_key": ""},
                "messenger": {
                    "telegram_bot_token": "token",
                    "telegram_chat_id": "12345",
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("GEMINI_API_KEY", "env-key")

    config = load_config(str(cfg_path))

    assert config.llm.api_key == "env-key"
    assert config.schedule.days == ["mon", "wed"]


def test_load_config_rejects_invalid_day(tmp_path):
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text(
        json.dumps(
            {
                "schedule": {"time": "09:30", "days": ["noday"], "timezone": "UTC"},
                "calendar": {"ical_url": "https://example.com/a.ics"},
                "llm": {"model": "gemini-2.0-flash", "api_key": "k"},
                "messenger": {
                    "telegram_bot_token": "token",
                    "telegram_chat_id": "12345",
                },
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="invalid schedule days"):
        load_config(str(cfg_path))
