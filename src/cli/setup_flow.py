from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from src.cli.calendar_setup import prompt_ical_urls
from src.cli.constants import (
    DEFAULT_MODEL,
    DEFAULT_SCHEDULE_DAYS,
    DEFAULT_SCHEDULE_TIME,
    DEFAULT_TIMEZONE,
    TIMEZONE_OPTIONS,
)
from src.cli.launchd import install_gateway, install_service
from src.cli.prompts import prompt_optional, prompt_required
from src.cli.telegram_setup import prompt_chat_id
from src.config import _validate_days, _validate_time


def _prompt_timezone_index(default: str | None = None) -> str:
    for idx, tz in enumerate(TIMEZONE_OPTIONS):
        print(f"{idx}: {tz}")
    if default is None:
        default = DEFAULT_TIMEZONE if DEFAULT_TIMEZONE in TIMEZONE_OPTIONS else None
    while True:
        prompt = "Timezone index"
        if default is not None:
            prompt += f" [{TIMEZONE_OPTIONS.index(default)}]"
        prompt += ": "
        value = input(prompt).strip()
        if not value and default is not None:
            return default
        if not value.isdigit():
            print("Timezone index must be a number.", file=sys.stderr)
            continue
        index = int(value)
        if 0 <= index < len(TIMEZONE_OPTIONS):
            return TIMEZONE_OPTIONS[index]
        print(f"Timezone index must be between 0 and {len(TIMEZONE_OPTIONS) - 1}.", file=sys.stderr)


def _maybe_install_launchd(config_path: Path) -> None:
    if sys.platform != "darwin":
        return
    install = prompt_optional("Install launchd agent for background runs? (y/N)") or "n"
    if install.lower() not in {"y", "yes"}:
        return
    confirm = prompt_optional("Type 'install' to confirm") or ""
    if confirm.strip().lower() != "install":
        print("Launchd install canceled.")
        return
    install_service(config_path)
    install_gateway(config_path)


def _install_both_services(config_path: Path) -> None:
    install_service(config_path)
    install_gateway(config_path)


def setup_config(path: Path, force: bool, install_mode: str = "prompt") -> None:
    if path.exists() and not force:
        print(f"Config file already exists: {path}", file=sys.stderr)
        print("Use --force to overwrite.", file=sys.stderr)
        raise SystemExit(2)

    while True:
        raw_time = prompt_required("Schedule time (HH:MM)", DEFAULT_SCHEDULE_TIME)
        try:
            schedule_time = _validate_time(raw_time)
            break
        except ValueError as exc:
            print(str(exc), file=sys.stderr)

    while True:
        raw_days = prompt_required("Schedule days (comma-separated)", DEFAULT_SCHEDULE_DAYS)
        try:
            schedule_days = _validate_days([d.strip() for d in raw_days.split(",") if d.strip()])
            break
        except ValueError as exc:
            print(str(exc), file=sys.stderr)

    print("Timezone options:")
    schedule_tz = _prompt_timezone_index(DEFAULT_TIMEZONE)
    ical_urls = prompt_ical_urls()
    llm_model = prompt_required("LLM model", DEFAULT_MODEL)
    llm_api_key = prompt_required("LLM API key", secret=True)
    telegram_bot_token = prompt_required("Telegram bot token", secret=True)
    telegram_chat_id = prompt_chat_id(telegram_bot_token)

    config: dict[str, Any] = {
        "schedule": {
            "time": schedule_time,
            "days": schedule_days,
            "timezone": schedule_tz,
        },
        "calendar": {"ical_urls": ical_urls},
        "llm": {"model": llm_model, "api_key": llm_api_key},
        "messenger": {
            "telegram_bot_token": telegram_bot_token,
            "telegram_chat_id": telegram_chat_id,
        },
    }

    from src.cli.config_ops import _save_config

    _save_config(path, config)
    print(f"Wrote config to {path}")
    if install_mode == "prompt":
        _maybe_install_launchd(path)
    elif install_mode == "both":
        _install_both_services(path)
