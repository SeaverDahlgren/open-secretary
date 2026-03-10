from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

WEEKDAYS = {"mon", "tue", "wed", "thu", "fri", "sat", "sun"}


@dataclass(slots=True)
class ScheduleConfig:
    time: str
    days: list[str]
    timezone: str


@dataclass(slots=True)
class CalendarConfig:
    ical_urls: list[str]


@dataclass(slots=True)
class LLMConfig:
    model: str
    api_key: str


@dataclass(slots=True)
class MessengerConfig:
    telegram_bot_token: str
    telegram_chat_id: str


@dataclass(slots=True)
class AppConfig:
    schedule: ScheduleConfig
    calendar: CalendarConfig
    llm: LLMConfig
    messenger: MessengerConfig


def _validate_time(value: str) -> str:
    parts = value.split(":")
    if len(parts) != 2:
        raise ValueError("schedule.time must be HH:MM")
    hour, minute = parts
    if not (hour.isdigit() and minute.isdigit()):
        raise ValueError("schedule.time must be numeric HH:MM")
    h = int(hour)
    m = int(minute)
    if h < 0 or h > 23 or m < 0 or m > 59:
        raise ValueError("schedule.time must be valid 24h HH:MM")
    return f"{h:02d}:{m:02d}"


def _validate_days(days: list[str]) -> list[str]:
    normalized = [d.strip().lower()[:3] for d in days]
    invalid = [d for d in normalized if d not in WEEKDAYS]
    if invalid:
        raise ValueError(f"invalid schedule days: {invalid}")
    return normalized


def load_config(path: str = "config.json") -> AppConfig:
    config_path = Path(path)
    raw = json.loads(config_path.read_text(encoding="utf-8"))

    schedule = raw.get("schedule", {})
    calendar = raw.get("calendar", {})
    llm = raw.get("llm", {})
    messenger = raw.get("messenger", {})

    llm_api_key = llm.get("api_key") or os.getenv("GEMINI_API_KEY", "")

    ical_urls: list[str] = []
    if isinstance(calendar, dict):
        raw_urls = calendar.get("ical_urls")
        if isinstance(raw_urls, list):
            ical_urls = [str(url).strip() for url in raw_urls if str(url).strip()]
        elif calendar.get("ical_url"):
            ical_urls = [str(calendar.get("ical_url")).strip()]

    cfg = AppConfig(
        schedule=ScheduleConfig(
            time=_validate_time(schedule.get("time", "08:00")),
            days=_validate_days(schedule.get("days", ["mon", "tue", "wed", "thu", "fri"])),
            timezone=schedule.get("timezone", "UTC"),
        ),
        calendar=CalendarConfig(
            ical_urls=ical_urls,
        ),
        llm=LLMConfig(
            model=llm.get("model", "gemini-2.5-flash"),
            api_key=llm_api_key,
        ),
        messenger=MessengerConfig(
            telegram_bot_token=messenger.get("telegram_bot_token", ""),
            telegram_chat_id=str(messenger.get("telegram_chat_id", "")),
        ),
    )

    if not cfg.calendar.ical_urls:
        raise ValueError("calendar.ical_urls (or calendar.ical_url) is required")
    if not cfg.llm.api_key:
        raise ValueError("llm.api_key or GEMINI_API_KEY is required")
    if not cfg.messenger.telegram_bot_token:
        raise ValueError("messenger.telegram_bot_token is required")
    if not cfg.messenger.telegram_chat_id:
        raise ValueError("messenger.telegram_chat_id is required")

    return cfg
