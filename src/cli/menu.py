from __future__ import annotations

from pathlib import Path
from typing import Any

from src.cli.calendar_setup import prompt_ical_urls
from src.cli.config_ops import load_config_file, save_config_file
from src.cli.launchd import install_gateway, install_service, stop_gateway, uninstall_gateway, uninstall_service
from src.cli.prompts import prompt_optional, prompt_required
from src.cli.setup_flow import setup_config


def run_menu(config_path: Path) -> None:
    while True:
        print("")
        print("openSecretary menu")
        print("1) Start/setup + install services")
        print("2) Add calendars")
        print("3) Delete calendars")
        print("4) Stop bot entirely")
        print("5) Uninstall services")
        print("6) Exit")
        choice = prompt_required("Select option").strip()
        if choice == "1":
            _start_flow(config_path)
        elif choice == "2":
            _add_calendars(config_path)
        elif choice == "3":
            _delete_calendars(config_path)
        elif choice == "4":
            _stop_bot(config_path)
        elif choice == "5":
            _uninstall_services()
        elif choice == "6":
            return
        else:
            print("Invalid option.")


def _add_calendars(config_path: Path) -> None:
    data = load_config_file(config_path)
    calendar = _ensure_section(data, "calendar")
    existing = _normalized_urls(calendar.get("ical_urls"))
    new_urls = prompt_ical_urls()
    merged = existing + [u for u in new_urls if u not in existing]
    calendar["ical_urls"] = merged
    save_config_file(config_path, data)
    print("Calendars updated.")


def _delete_calendars(config_path: Path) -> None:
    data = load_config_file(config_path)
    calendar = _ensure_section(data, "calendar")
    urls = _normalized_urls(calendar.get("ical_urls"))
    if not urls:
        print("No calendars configured.")
        return
    print("Configured calendars:")
    for idx, url in enumerate(urls):
        print(f"{idx}: {url}")
    raw = prompt_optional("Indices to delete (comma-separated)")
    if not raw:
        return
    indices = _parse_indices(raw, len(urls))
    if not indices:
        print("No valid indices selected.")
        return
    remaining = [url for idx, url in enumerate(urls) if idx not in indices]
    calendar["ical_urls"] = remaining
    save_config_file(config_path, data)
    print("Calendars updated.")


def _uninstall_services() -> None:
    uninstall_service()
    uninstall_gateway()


def _stop_bot(config_path: Path) -> None:
    data = load_config_file(config_path)
    agent = _ensure_section(data, "agent")
    agent["enabled"] = False
    save_config_file(config_path, data)
    stop_gateway()
    print("Bot disabled. Re-enable by setting agent.enabled to true.")


def _start_flow(config_path: Path) -> None:
    if config_path.exists():
        reinstall = prompt_optional("Config exists. Reinstall services? (y/N)") or "n"
        if reinstall.lower() in {"y", "yes"}:
            install_service(config_path)
            install_gateway(config_path)
            print("Services installed.")
        return
    setup_config(config_path, force=False, install_mode="both")


def _ensure_section(data: dict[str, Any], key: str) -> dict[str, Any]:
    section = data.get(key)
    if not isinstance(section, dict):
        section = {}
        data[key] = section
    return section


def _normalized_urls(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(url).strip() for url in value if str(url).strip()]
    return []


def _parse_indices(raw: str, max_len: int) -> set[int]:
    indices: set[int] = set()
    for part in raw.split(","):
        token = part.strip()
        if not token.isdigit():
            continue
        idx = int(token)
        if 0 <= idx < max_len:
            indices.add(idx)
    return indices
