from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.text import Text

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
from src.cli.prompts import prompt_optional, prompt_required
from src.cli.setup_flow import setup_config


def run_menu(config_path: Path) -> None:
    console = Console()
    _render_banner(console)
    while True:
        console.clear()
        _render_banner(console)
        choice = _select_option(
            "Main menu",
            [
                ("c", "Configure calendars 📅"),
                ("b", "Configure bots 🤖"),
                ("m", "Model configs 🧠"),
                ("u", "Uninstall openSecretary 🧹"),
                ("q", "Exit"),
            ],
        )
        if choice in {"c", "calendars"}:
            _calendar_menu(console, config_path)
        elif choice in {"b", "bots"}:
            _bots_menu(console, config_path)
        elif choice in {"m", "models"}:
            _model_menu(console, config_path)
        elif choice in {"u", "uninstall"}:
            _uninstall_services(console)
        elif choice in {"q", "exit"} or choice is None:
            return


def _add_calendars(console: Console, config_path: Path) -> None:
    data = load_config_file(config_path)
    calendar = _ensure_section(data, "calendar")
    existing = _normalized_urls(calendar.get("ical_urls"))
    new_urls = prompt_ical_urls()
    merged = existing + [u for u in new_urls if u not in existing]
    calendar["ical_urls"] = merged
    save_config_file(config_path, data)
    console.print("[green]Calendars updated.[/green]")


def _delete_calendars(console: Console, config_path: Path) -> None:
    data = load_config_file(config_path)
    calendar = _ensure_section(data, "calendar")
    urls = _normalized_urls(calendar.get("ical_urls"))
    if not urls:
        console.print("[yellow]No calendars configured.[/yellow]")
        return
    console.print("Configured calendars:")
    for idx, url in enumerate(urls):
        console.print(f"{idx}: {url}")
    raw = prompt_optional("Indices to delete (comma-separated)")
    if not raw:
        return
    indices = _parse_indices(raw, len(urls))
    if not indices:
        console.print("[yellow]No valid indices selected.[/yellow]")
        return
    remaining = [url for idx, url in enumerate(urls) if idx not in indices]
    calendar["ical_urls"] = remaining
    save_config_file(config_path, data)
    console.print("[green]Calendars updated.[/green]")


def _uninstall_services(console: Console) -> None:
    confirm = prompt_required(
        "Uninstalling will clear bot memory. Type 'uninstall' to continue"
    ).strip()
    if confirm.lower() != "uninstall":
        console.print("[yellow]Uninstall canceled.[/yellow]")
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
    Console().print("[green]Bot disabled.[/green] Re-enable by setting agent.enabled to true.")


def _calendar_menu(console: Console, config_path: Path) -> None:
    while True:
        console.clear()
        _render_banner(console)
        choice = _select_option(
            "Calendars",
            [
                ("a", "Add calendars ➕"),
                ("d", "Delete calendars ➖"),
                ("b", "Back"),
            ],
        )
        if choice in {"a", "add"}:
            _add_calendars(console, config_path)
        elif choice in {"d", "delete"}:
            _delete_calendars(console, config_path)
        elif choice in {"b", "back"} or choice is None:
            return


def _bots_menu(console: Console, config_path: Path) -> None:
    data = load_config_file(config_path)
    agent = _ensure_section(data, "agent")
    agent_enabled = bool(agent.get("enabled", True))
    reminders_state = service_state("com.opensecretary")
    gateway_state = service_state("com.opensecretary.gateway")
    reminders_enabled = reminders_state in {"running", "loaded"}
    gateway_enabled = gateway_state in {"running", "loaded"} and agent_enabled

    console.clear()
    _render_banner(console)
    console.print("Bots")
    console.print(
        f"Daily reminders: {'enabled' if reminders_enabled else 'disabled'} ({reminders_state})"
    )
    console.print(
        f"Gateway: {'enabled' if gateway_enabled else 'disabled'} ({gateway_state})"
    )

    if reminders_enabled:
        reminders_label = "Disable daily reminders"
    else:
        reminders_label = "Enable daily reminders"
    if gateway_enabled:
        gateway_label = "Disable gateway"
    else:
        gateway_label = "Enable gateway"
    choice = _select_option(
        "Bots",
        [
            ("r", reminders_label),
            ("g", gateway_label),
            ("b", "Back"),
        ],
    )
    if choice in {"b", "back"} or choice is None:
        return
    if choice == "r":
        if reminders_enabled:
            action = "disable-reminders"
        else:
            action = "enable-reminders"
    elif choice == "g":
        if gateway_enabled:
            action = "disable-gateway"
        else:
            action = "enable-gateway"
    else:
        console.print("[red]Invalid option.[/red]")
        return
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


def _model_menu(console: Console, config_path: Path) -> None:
    data = load_config_file(config_path)
    llm = _ensure_section(data, "llm")
    current_model = llm.get("model") or ""
    console.clear()
    _render_banner(console)
    console.print("Model configs")
    console.print(f"Current model: {current_model or '(not set)'}")
    new_model = prompt_optional("New model (leave blank to keep current)") or ""
    if new_model.strip():
        llm["model"] = new_model.strip()
    new_key = prompt_optional("New API key (leave blank to keep current)", secret=True) or ""
    if new_key.strip():
        llm["api_key"] = new_key.strip()
    save_config_file(config_path, data)
    console.print("[green]Model settings updated.[/green]")


def _clear_bot_memory() -> None:
    try:
        from src.config import load_config

        cfg = load_config()
        memory_path = Path(cfg.agent.memory_path)
    except Exception:
        memory_path = Path("agent_memory.md")
    if memory_path.exists():
        subprocess.run(["trash", str(memory_path)], check=False)


def _render_banner(console: Console) -> None:
    console.print(Text(_render_banner_text(), style="bold magenta"))


def _render_banner_text() -> str:
    return """
           ____                  _____                     __
          / __ \\____  ___  ____ / ___/___  _____________  / /_____ ________  __
         / / / / __ \\/ _ \\/ __ \\\\__ \\/ _ \\/ ___/ ___/ _ \\/ __/ __ `/ ___/ / / /
        / /_/ / /_/ /  __/ / / /__/ /  __/ /__/ /  /  __/ /_/ /_/ / /  / /_/ /
        \\____/ .___/\\___/_/ /_/____/\\___/\\___/_/   \\___/\\__/\\__,_/_/   \\__, /
            /_/                                                       /____/
    """


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


def _select_option(title: str, options: list[tuple[str, str]]) -> str | None:
    index = 0
    result: dict[str, str | None] = {"value": None}
    banner = _render_banner_text()

    def _render():
        lines: list[tuple[str, str]] = [
            ("bold magenta", banner),
            ("", "\n"),
            ("bold cyan", f"{title}\n\n"),
        ]
        for idx, (_, label) in enumerate(options):
            if idx == index:
                lines.append(("bold cyan", f"> {label}\n"))
            else:
                lines.append(("", f"  {label}\n"))
        lines.append(("", "\nUse ↑/↓ or j/k, Enter to select, q to cancel."))
        return lines

    control = FormattedTextControl(_render)
    layout = Layout(HSplit([Window(content=control)]))

    kb = KeyBindings()

    @kb.add("up")
    @kb.add("k")
    def _up(event) -> None:
        nonlocal index
        index = (index - 1) % len(options)

    @kb.add("down")
    @kb.add("j")
    def _down(event) -> None:
        nonlocal index
        index = (index + 1) % len(options)

    @kb.add("enter")
    def _enter(event) -> None:
        result["value"] = options[index][0]
        event.app.exit()

    @kb.add("escape")
    @kb.add("q")
    def _quit(event) -> None:
        event.app.exit()

    app = Application(layout=layout, key_bindings=kb, full_screen=True, style=Style([]))
    app.run()
    return result["value"]
