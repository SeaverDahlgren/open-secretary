from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.cli.constants import SENSITIVE_PATHS
from src.config import _validate_days, _validate_time


def _load_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _save_config(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(data, indent=2, sort_keys=True)
    path.write_text(content + "\n", encoding="utf-8")


def _ensure_section(data: dict[str, Any], key: str) -> dict[str, Any]:
    section = data.get(key)
    if not isinstance(section, dict):
        section = {}
        data[key] = section
    return section


def _normalize_days(days: str) -> list[str]:
    parts = [d.strip() for d in days.split(",") if d.strip()]
    return _validate_days(parts)


def set_schedule(
    path: Path, time_value: str | None, days_value: str | None, timezone: str | None
) -> None:
    if not any([time_value, days_value, timezone, timezone_index is not None]):
        raise SystemExit("Provide at least one of --time, --days, --timezone, or --timezone-index.")

    data = _load_config(path)
    schedule = _ensure_section(data, "schedule")

    if time_value:
        schedule["time"] = _validate_time(time_value)
    if days_value:
        schedule["days"] = _normalize_days(days_value)
    if timezone:
        schedule["timezone"] = timezone

    _save_config(path, data)
    print(f"Updated schedule in {path}")


def set_calendar(path: Path, ical_urls: list[str] | None) -> None:
    if not ical_urls:
        raise SystemExit("Provide --ical-url or --ical-urls.")
    data = _load_config(path)
    calendar = _ensure_section(data, "calendar")
    calendar["ical_urls"] = ical_urls
    calendar.pop("ical_url", None)
    _save_config(path, data)
    print(f"Updated calendar in {path}")


def set_llm(path: Path, model: str | None, api_key: str | None) -> None:
    if not any([model, api_key]):
        raise SystemExit("Provide --model, --api-key, or --prompt-api-key.")

    data = _load_config(path)
    llm = _ensure_section(data, "llm")

    if model:
        llm["model"] = model
    if api_key:
        llm["api_key"] = api_key

    _save_config(path, data)
    print(f"Updated LLM settings in {path}")


def set_messenger(path: Path, bot_token: str | None, chat_id: str | None) -> None:
    if not any([bot_token, chat_id]):
        raise SystemExit("Provide --bot-token, --chat-id, or --prompt-bot-token.")

    data = _load_config(path)
    messenger = _ensure_section(data, "messenger")

    if bot_token:
        messenger["telegram_bot_token"] = bot_token
    if chat_id:
        messenger["telegram_chat_id"] = chat_id

    _save_config(path, data)
    print(f"Updated messenger settings in {path}")


def redact_config(data: dict[str, Any]) -> dict[str, Any]:
    redacted = json.loads(json.dumps(data))
    for section_key, field_key in SENSITIVE_PATHS:
        section = redacted.get(section_key)
        if isinstance(section, dict) and field_key in section:
            section[field_key] = "REDACTED"
    return redacted


def show_config(path: Path) -> None:
    data = _load_config(path)
    redacted = redact_config(data)
    print(json.dumps(redacted, indent=2, sort_keys=True))


def load_config_file(path: Path) -> dict[str, Any]:
    return _load_config(path)


def save_config_file(path: Path, data: dict[str, Any]) -> None:
    _save_config(path, data)
