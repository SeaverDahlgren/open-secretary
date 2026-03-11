from __future__ import annotations

from pathlib import Path

from src.cli.config_ops import set_calendar, set_llm, set_messenger, set_schedule, show_config
from src.cli.constants import TIMEZONE_OPTIONS
from src.cli.launchd import install_service, service_status, uninstall_service
from src.cli.parser import build_parser
from src.cli.prompts import prompt_optional
from src.cli.setup_flow import setup_config
from src.config import load_config
from src.pipeline import DailySummaryPipeline


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    config_path = Path(args.config)

    if args.command == "setup":
        setup_config(config_path, force=args.force)
    elif args.command == "set-schedule":
        timezone = args.timezone
        if args.timezone_index is not None:
            if args.timezone_index < 0 or args.timezone_index >= len(TIMEZONE_OPTIONS):
                raise SystemExit(
                    f"--timezone-index must be between 0 and {len(TIMEZONE_OPTIONS) - 1}."
                )
            timezone = TIMEZONE_OPTIONS[args.timezone_index]
        set_schedule(config_path, args.time, args.days, timezone)
    elif args.command == "set-calendar":
        urls: list[str] = []
        if args.ical_urls:
            urls.extend([u.strip() for u in args.ical_urls.split(",") if u.strip()])
        if args.ical_url:
            urls.extend([u.strip() for u in args.ical_url if u and u.strip()])
        set_calendar(config_path, urls or None)
    elif args.command == "set-llm":
        api_key = args.api_key
        if api_key is None and args.prompt_api_key:
            api_key = prompt_optional("LLM API key", secret=True)
        set_llm(config_path, args.model, api_key)
    elif args.command == "set-messenger":
        bot_token = args.bot_token
        if bot_token is None and args.prompt_bot_token:
            bot_token = prompt_optional("Telegram bot token", secret=True)
        set_messenger(config_path, bot_token, args.chat_id)
    elif args.command == "show":
        show_config(config_path)
    elif args.command == "run-now":
        config = load_config(str(config_path))
        pipeline = DailySummaryPipeline(config)
        message_id = pipeline.run()
        print(f"Sent Telegram message {message_id}")
    elif args.command == "install-service":
        install_service(config_path)
    elif args.command == "uninstall-service":
        uninstall_service()
    elif args.command == "status":
        service_status()
    else:
        parser.error("Unknown command")


if __name__ == "__main__":
    main()
