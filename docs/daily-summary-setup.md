# Daily Summary Setup

## Requirements

- Python 3.11+
- Telegram bot token + chat id
- Gemini API key
- iCal/ICS feed URL(s)

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

## Configure

Option A: interactive CLI

```bash
python cli.py setup
```

Option B: edit `config.json`

- `calendar.ical_urls` list
- `llm.model`
- `llm.api_key` or `GEMINI_API_KEY`
- `messenger.telegram_bot_token`
- `messenger.telegram_chat_id`
- `schedule.time` (`HH:MM`)
- `schedule.days` (`mon..sun`)
- `schedule.timezone` (`America/Los_Angeles`, `UTC`, etc)

Finding iCal URLs

- Most calendar providers expose an iCal/ICS feed link in calendar settings or sharing options.
- The CLI can prompt you to add iCloud calendar iCal URLs during setup.
- On My Mac calendars are not supported.
- Google Calendar: Settings for the calendar > Integrate calendar > copy “Secret address in iCal format”.

## Run

```bash
python -m src.main
```

Run once

```bash
python cli.py run-now
```

## macOS Service

```bash
python cli.py install-service
python cli.py status
python cli.py uninstall-service
```

## Test

```bash
pytest
```

## Troubleshooting

- `calendar.ical_urls is required`: missing calendar feed URL(s)
- `llm.api_key or GEMINI_API_KEY is required`: missing Gemini credentials
- `messenger.telegram_bot_token is required`: missing bot token
- `messenger.telegram_chat_id is required`: run `python cli.py setup` to fetch chat id
