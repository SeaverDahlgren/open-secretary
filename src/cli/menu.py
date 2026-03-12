from __future__ import annotations

from pathlib import Path
import subprocess
from typing import Any

from src.cli.calendar_setup import prompt_ical_urls
from src.cli.config_ops import load_config_file, save_config_file
from src.cli.launchd import (
    install_gateway,
    install_service,
    service_state,
    stop_gateway,
    stop_service,
    uninstall_gateway,
    uninstall_service,
)
from src.cli.prompts import prompt_required
from src.cli.setup_flow import setup_config


def run_menu(config_path: Path) -> None:
    while True:
        print("")
        print("openSecretary menu")
        print("1) Configure calendars")
        print("2) Configure bots")
        print("3) Uninstall openSecretary")
        print("4) Exit")
        choice = prompt_required("Select option").strip()
        if choice == "1":
            _calendar_menu(config_path)
        elif choice == "2":
            _bots_menu(config_path)
        elif choice == "3":
            _uninstall_services()
        elif choice == "4":
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
    confirm = prompt_required(
        "Uninstalling will clear bot memory. Type 'uninstall' to continue"
    ).strip()
    if confirm.lower() != "uninstall":
        print("Uninstall canceled.")
        return
    _clear_bot_memory()
    uninstall_service()
    uninstall_gateway()


def _stop_bot(config_path: Path) -> None:
    data = load_config_file(config_path)
    agent = _ensure_section(data, "agent")
    agent["enabled"] = False
    save_config_file(config_path, data)
    stop_gateway()
    print("Bot disabled. Re-enable by setting agent.enabled to true.")


def _calendar_menu(config_path: Path) -> None:
    while True:
        print("")
        print("Calendars")
        print("1) Add calendars")
        print("2) Delete calendars")
        print("3) Back")
        choice = prompt_required("Select option").strip()
        if choice == "1":
            _add_calendars(config_path)
        elif choice == "2":
            _delete_calendars(config_path)
        elif choice == "3":
            return
        else:
            print("Invalid option.")


def _bots_menu(config_path: Path) -> None:
    data = load_config_file(config_path)
    agent = _ensure_section(data, "agent")
    agent_enabled = bool(agent.get("enabled", True))
    reminders_state = service_state("com.opensecretary")
    gateway_state = service_state("com.opensecretary.gateway")
    reminders_enabled = reminders_state in {"running", "loaded"}
    gateway_enabled = gateway_state in {"running", "loaded"} and agent_enabled

    print("")
    print(f"Daily reminders: {'enabled' if reminders_enabled else 'disabled'} ({reminders_state})")
    print(f"Gateway: {'enabled' if gateway_enabled else 'disabled'} ({gateway_state})")

    options: list[tuple[str, str]] = []
    if reminders_enabled:
        options.append(("Disable daily reminders", "disable-reminders"))
    else:
        options.append(("Enable daily reminders", "enable-reminders"))
    if gateway_enabled:
        options.append(("Disable gateway", "disable-gateway"))
    else:
        options.append(("Enable gateway", "enable-gateway"))
    options.append(("Back", "back"))

    for idx, (label, _) in enumerate(options, start=1):
        print(f"{idx}) {label}")
    choice = prompt_required("Select option").strip()
    if not choice.isdigit():
        print("Invalid option.")
        return
    index = int(choice) - 1
    if index < 0 or index >= len(options):
        print("Invalid option.")
        return
    action = options[index][1]
    if action == "enable-reminders":
        _ensure_config_exists(config_path)
        install_service(config_path)
    elif action == "disable-reminders":
        stop_service()
    elif action == "enable-gateway":
        _ensure_config_exists(config_path)
        agent["enabled"] = True
        save_config_file(config_path, data)
        install_gateway(config_path)
    elif action == "disable-gateway":
        agent["enabled"] = False
        save_config_file(config_path, data)
        stop_gateway()
    return


def _ensure_config_exists(config_path: Path) -> None:
    if not config_path.exists():
        setup_config(config_path, force=False, install_mode="none")


def _clear_bot_memory() -> None:
    try:
        from src.config import load_config

        cfg = load_config()
        memory_path = Path(cfg.agent.memory_path)
    except Exception:
        memory_path = Path("agent_memory.md")
    if memory_path.exists():
        subprocess.run(["trash", str(memory_path)], check=False)


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
