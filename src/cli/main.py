from __future__ import annotations

import argparse
import json
import os
import plistlib
import subprocess
import sys
from pathlib import Path
from typing import Any

import requests

from src.cli.calendar_setup import prompt_ical_urls
from src.cli.prompts import prompt_optional, prompt_required
from src.config import _validate_days, _validate_time, load_config
from src.pipeline import DailySummaryPipeline

DEFAULT_SCHEDULE_TIME = "08:00"
DEFAULT_SCHEDULE_DAYS = "mon,tue,wed,thu,fri"
DEFAULT_TIMEZONE = "UTC"
DEFAULT_MODEL = "gemini-2.5-flash"

TIMEZONE_OPTIONS = [
    "UTC",
    "America/Los_Angeles",
    "America/Denver",
    "America/Chicago",
    "America/New_York",
    "Europe/London",
    "Europe/Paris",
    "Europe/Berlin",
    "Asia/Tokyo",
    "Asia/Shanghai",
    "Asia/Singapore",
    "Australia/Sydney",
]

SENSITIVE_PATHS: set[tuple[str, str]] = {
    ("llm", "api_key"),
    ("messenger", "telegram_bot_token"),
}


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


def _prompt_ical_urls() -> list[str]:
    return prompt_ical_urls()


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


def _setup_config(path: Path, force: bool) -> None:
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
            schedule_days = _normalize_days(raw_days)
            break
        except ValueError as exc:
            print(str(exc), file=sys.stderr)

    print("Timezone options:")
    schedule_tz = _prompt_timezone_index(DEFAULT_TIMEZONE)
    ical_urls = _prompt_ical_urls()
    llm_model = prompt_required("LLM model", DEFAULT_MODEL)
    llm_api_key = prompt_required("LLM API key", secret=True)
    telegram_bot_token = prompt_required("Telegram bot token", secret=True)
    telegram_chat_id = _prompt_chat_id(telegram_bot_token)

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
    _save_config(path, config)
    print(f"Wrote config to {path}")
    _maybe_install_launchd(path)


def _set_schedule(
    path: Path, time_value: str | None, days_value: str | None, timezone: str | None, timezone_index: int | None
) -> None:
    if not any([time_value, days_value, timezone, timezone_index is not None]):
        raise SystemExit("Provide at least one of --time, --days, --timezone, or --timezone-index.")

    data = _load_config(path)
    schedule = _ensure_section(data, "schedule")

    if time_value:
        schedule["time"] = _validate_time(time_value)
    if days_value:
        schedule["days"] = _normalize_days(days_value)
    if timezone_index is not None:
        if timezone_index < 0 or timezone_index >= len(TIMEZONE_OPTIONS):
            raise SystemExit(f"--timezone-index must be between 0 and {len(TIMEZONE_OPTIONS) - 1}.")
        schedule["timezone"] = TIMEZONE_OPTIONS[timezone_index]
    elif timezone:
        schedule["timezone"] = timezone

    _save_config(path, data)
    print(f"Updated schedule in {path}")


def _set_calendar(
    path: Path,
    ical_urls: list[str] | None,
) -> None:
    if not ical_urls:
        raise SystemExit("Provide --ical-url or --ical-urls.")
    data = _load_config(path)
    calendar = _ensure_section(data, "calendar")
    calendar["ical_urls"] = ical_urls
    calendar.pop("ical_url", None)
    _save_config(path, data)
    print(f"Updated calendar in {path}")


def _set_llm(path: Path, model: str | None, api_key: str | None, prompt_api_key: bool) -> None:
    if not any([model, api_key, prompt_api_key]):
        raise SystemExit("Provide --model, --api-key, or --prompt-api-key.")

    data = _load_config(path)
    llm = _ensure_section(data, "llm")

    if model:
        llm["model"] = model
    if api_key is None and prompt_api_key:
        api_key = prompt_optional("LLM API key", secret=True)
    if api_key:
        llm["api_key"] = api_key

    _save_config(path, data)
    print(f"Updated LLM settings in {path}")


def _set_messenger(
    path: Path, bot_token: str | None, chat_id: str | None, prompt_bot_token: bool
) -> None:
    if not any([bot_token, chat_id, prompt_bot_token]):
        raise SystemExit("Provide --bot-token, --chat-id, or --prompt-bot-token.")

    data = _load_config(path)
    messenger = _ensure_section(data, "messenger")

    if bot_token is None and prompt_bot_token:
        bot_token = prompt_optional("Telegram bot token", secret=True)
    if bot_token:
        messenger["telegram_bot_token"] = bot_token
    if chat_id:
        messenger["telegram_chat_id"] = chat_id

    _save_config(path, data)
    print(f"Updated messenger settings in {path}")


def _redact_config(data: dict[str, Any]) -> dict[str, Any]:
    redacted = json.loads(json.dumps(data))
    for section_key, field_key in SENSITIVE_PATHS:
        section = redacted.get(section_key)
        if isinstance(section, dict) and field_key in section:
            section[field_key] = "REDACTED"
    return redacted


def _show_config(path: Path) -> None:
    data = _load_config(path)
    redacted = _redact_config(data)
    print(json.dumps(redacted, indent=2, sort_keys=True))


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


def _prompt_chat_id(bot_token: str) -> str:
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
    _install_service(config_path)


def _write_launchd_plist(plist_path: Path, project_root: Path) -> None:
    plist_path.parent.mkdir(parents=True, exist_ok=True)
    log_dir = Path.home() / "Library" / "Logs"
    plist = {
        "Label": "com.opensecretary",
        "ProgramArguments": [sys.executable, "-m", "src.main"],
        "WorkingDirectory": str(project_root),
        "RunAtLoad": True,
        "KeepAlive": True,
        "StandardOutPath": str(log_dir / "openSecretary.log"),
        "StandardErrorPath": str(log_dir / "openSecretary.log"),
        "EnvironmentVariables": {
            "PYTHONPATH": str(project_root),
        },
    }
    with plist_path.open("wb") as handle:
        plistlib.dump(plist, handle)


def _bootstrap_launchd(plist_path: Path, label: str) -> None:
    uid = os.getuid()
    target = f"gui/{uid}"
    subprocess.run(["launchctl", "bootout", target, str(plist_path)], check=False)
    subprocess.run(["launchctl", "bootstrap", target, str(plist_path)], check=True)
    subprocess.run(["launchctl", "kickstart", "-k", f"{target}/{label}"], check=False)


def _service_label() -> str:
    return "com.opensecretary"


def _service_plist_path() -> Path:
    return Path.home() / "Library" / "LaunchAgents" / f"{_service_label()}.plist"


def _install_service(config_path: Path) -> None:
    if sys.platform != "darwin":
        raise SystemExit("install-service is only supported on macOS.")

    project_root = Path(__file__).resolve().parents[2]
    config_path = config_path.resolve()
    if config_path.parent != project_root or config_path.name != "config.json":
        raise SystemExit(
            f"install-service requires {project_root / 'config.json'}."
        )

    plist_path = _service_plist_path()
    print(f"Writing launchd plist to {plist_path}")
    _write_launchd_plist(plist_path, project_root)
    _bootstrap_launchd(plist_path, _service_label())
    print("launchd service installed.")


def _uninstall_service() -> None:
    if sys.platform != "darwin":
        raise SystemExit("uninstall-service is only supported on macOS.")

    plist_path = _service_plist_path()
    uid = os.getuid()
    target = f"gui/{uid}"
    subprocess.run(["launchctl", "bootout", target, str(plist_path)], check=False)
    if plist_path.exists():
        subprocess.run(["trash", str(plist_path)], check=True)
        print("launchd plist moved to Trash.")
    else:
        print("launchd plist not found.")


def _service_status() -> None:
    if sys.platform != "darwin":
        raise SystemExit("status is only supported on macOS.")

    uid = os.getuid()
    target = f"gui/{uid}/{_service_label()}"
    plist_path = _service_plist_path()
    result = subprocess.run(
        ["launchctl", "print", target],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        state = "not loaded"
    elif "state = running" in result.stdout:
        state = "running"
    else:
        state = "loaded"
    print(f"Service: {state}")
    print(f"Plist: {plist_path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="openSecretary config CLI")
    parser.add_argument("--config", default="config.json", help="Path to config.json")
    subparsers = parser.add_subparsers(dest="command", required=True)

    setup_parser = subparsers.add_parser("setup", help="First-time interactive setup")
    setup_parser.add_argument("--force", action="store_true", help="Overwrite existing config")

    schedule_parser = subparsers.add_parser("set-schedule", help="Update schedule settings")
    schedule_parser.add_argument("--time", help="Time in HH:MM")
    schedule_parser.add_argument("--days", help="Comma-separated days, e.g. mon,wed,fri")
    schedule_parser.add_argument("--timezone", help="Timezone, e.g. America/Los_Angeles")
    schedule_parser.add_argument(
        "--timezone-index", type=int, help="Timezone option index from the setup list"
    )

    calendar_parser = subparsers.add_parser("set-calendar", help="Update calendar settings")
    calendar_parser.add_argument(
        "--ical-url", action="append", help="iCal URL (repeat for multiple)"
    )
    calendar_parser.add_argument(
        "--ical-urls", help="Comma-separated iCal URLs"
    )

    llm_parser = subparsers.add_parser("set-llm", help="Update LLM settings")
    llm_parser.add_argument("--model", help="Model name")
    llm_parser.add_argument("--api-key", help="LLM API key")
    llm_parser.add_argument(
        "--prompt-api-key", action="store_true", help="Prompt for API key"
    )

    messenger_parser = subparsers.add_parser("set-messenger", help="Update messenger settings")
    messenger_parser.add_argument("--bot-token", help="Telegram bot token")
    messenger_parser.add_argument("--chat-id", help="Telegram chat id")
    messenger_parser.add_argument(
        "--prompt-bot-token", action="store_true", help="Prompt for bot token"
    )

    subparsers.add_parser("show", help="Show current config with secrets redacted")
    subparsers.add_parser("run-now", help="Run the summary pipeline immediately")
    subparsers.add_parser("install-service", help="Install launchd service (macOS)")
    subparsers.add_parser("uninstall-service", help="Uninstall launchd service (macOS)")
    subparsers.add_parser("status", help="Show launchd service status (macOS)")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    config_path = Path(args.config)

    if args.command == "setup":
        _setup_config(config_path, force=args.force)
    elif args.command == "set-schedule":
        _set_schedule(config_path, args.time, args.days, args.timezone, args.timezone_index)
    elif args.command == "set-calendar":
        urls: list[str] = []
        if args.ical_urls:
            urls.extend([u.strip() for u in args.ical_urls.split(",") if u.strip()])
        if args.ical_url:
            urls.extend([u.strip() for u in args.ical_url if u and u.strip()])
        _set_calendar(config_path, urls or None)
    elif args.command == "set-llm":
        _set_llm(config_path, args.model, args.api_key, args.prompt_api_key)
    elif args.command == "set-messenger":
        _set_messenger(config_path, args.bot_token, args.chat_id, args.prompt_bot_token)
    elif args.command == "show":
        _show_config(config_path)
    elif args.command == "run-now":
        config = load_config(str(config_path))
        pipeline = DailySummaryPipeline(config)
        message_id = pipeline.run()
        print(f"Sent Telegram message {message_id}")
    elif args.command == "install-service":
        _install_service(config_path)
    elif args.command == "uninstall-service":
        _uninstall_service()
    elif args.command == "status":
        _service_status()
    else:
        parser.error("Unknown command")


if __name__ == "__main__":
    main()
