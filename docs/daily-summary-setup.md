# Daily Summary Setup

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

## Configure

1. Edit `config.json`.
2. Set calendar iCal URL(s).
3. Set Gemini API key (`llm.api_key` or `GEMINI_API_KEY`).
4. Set Telegram bot credentials (`messenger.telegram_bot_token`, `messenger.telegram_chat_id`).
5. Choose `schedule.time` (`HH:MM`) and `schedule.days` (`mon..sun`).
6. Optional: install the macOS launchd service via `python cli.py install-service`.

Finding iCal URLs

- Most calendar providers expose an iCal/ICS feed link in calendar settings or sharing options.
- The CLI can prompt you to add iCloud calendar iCal URLs during setup.
- On My Mac calendars are not supported.
- Google Calendar: Settings for the calendar > Integrate calendar > copy “Secret address in iCal format”.

## Run

```bash
python -m src.main
```

## Test

```bash
pytest
```
