# openSecretary

Daily calendar summary to Telegram using APScheduler + iCal + Gemini.

**Quickstart**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
python cli.py setup
python -m src.main
```

**CLI**

```bash
python cli.py setup
python cli.py set-schedule --time 08:00 --days mon,wed,fri --timezone-index 1
python cli.py set-calendar --ical-urls https://example.com/a.ics,https://example.com/b.ics
python cli.py set-llm --model gemini-2.5-flash --prompt-api-key
python cli.py run-now
python cli.py install-service
```

**Config Keys**

- `schedule.time`, `schedule.days`, `schedule.timezone`
- `calendar.ical_urls`
- `llm.model`, `llm.api_key` or `GEMINI_API_KEY`
- `messenger.telegram_bot_token`, `messenger.telegram_chat_id`
- `agent.*` (see `docs/gateway.md`)

**Architecture**

- `src/calendar`: fetches iCal data and maps it to `CalendarEvent` items.
- `src/cli`: manages config.json interactively or via commands.
- `src/gateway`: polls Telegram and runs the agent chat loop.
- `src/llm`: builds prompts and calls Gemini to generate the summary.
- `src/messenger`: sends the summary to Telegram.
- `src/scheduler`: schedules the daily job with APScheduler.
- `src/shared`: shared data models such as `CalendarEvent`.

**Docs**

- `docs/daily-summary-setup.md`: end-to-end setup
- `docs/calendar.md`: iCal parsing behavior
- `docs/gateway.md`: Telegram polling gateway
- `docs/llm.md`: prompt + Gemini usage
- `docs/messenger.md`: Telegram delivery details
- `docs/scheduler.md`: scheduling details

**Troubleshooting**

- `calendar.ical_urls is required`: missing calendar feed URL(s)
- `llm.api_key or GEMINI_API_KEY is required`: missing Gemini credentials
- `messenger.telegram_bot_token is required`: missing bot token
- `messenger.telegram_chat_id is required`: missing chat id
