from __future__ import annotations

import argparse


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
    subparsers.add_parser("install-gateway", help="Install gateway service (macOS)")
    subparsers.add_parser("uninstall-gateway", help="Uninstall gateway service (macOS)")
    subparsers.add_parser("gateway-status", help="Show gateway service status (macOS)")
    subparsers.add_parser("gateway-run", help="Run the gateway in the foreground")

    return parser
