---
summary: "CLI for creating and updating config.json without exposing secrets"
read_when:
  - "When changing configuration or setup workflow"
---

# CLI Package

Interactive and command-line config management for `config.json`.

Default entry point

- Running `python cli.py` with no subcommand opens the interactive menu.
- `manage` is an alias for the interactive menu.
- `setup` walks through first-time credentials and schedule.
- `start` runs setup and installs both services.
- `set-schedule`, `set-calendar`, `set-llm`, `set-messenger` update one area at a time.
- `run-now` triggers the pipeline immediately and sends the summary to Telegram.
- `install-service`, `uninstall-service`, `status` manage the macOS launchd service.
- `install-gateway`, `uninstall-gateway`, `gateway-status` manage the gateway service.
- `gateway-run` runs the gateway in the foreground.
- `menu` provides an interactive menu to manage calendars and services.
- `stop-bot` disables the bot and stops the gateway service.
- `uninstall-all` uninstalls both services.
- `show` prints config with secrets redacted.

Timezone options

- `0` = `UTC`
- `1` = `America/Los_Angeles`
- `2` = `America/Denver`
- `3` = `America/Chicago`
- `4` = `America/New_York`
- `5` = `Europe/London`
- `6` = `Europe/Paris`
- `7` = `Europe/Berlin`
- `8` = `Asia/Tokyo`
- `9` = `Asia/Shanghai`
- `10` = `Asia/Singapore`
- `11` = `Australia/Sydney`

Usage

```bash
python cli.py
python cli.py manage
python cli.py setup
python cli.py start
python cli.py set-schedule --time 08:00 --days mon,wed,fri --timezone-index 1
python cli.py set-calendar --ical-url https://example.com/cal.ics --ical-url https://example.com/other.ics
python cli.py set-calendar --ical-urls https://example.com/cal.ics,https://example.com/other.ics
python cli.py set-llm --model gemini-2.5-flash --prompt-api-key
python cli.py run-now
python cli.py install-service
python cli.py status
python cli.py uninstall-service
python cli.py install-gateway
python cli.py gateway-status
python cli.py uninstall-gateway
python cli.py gateway-run
python cli.py menu
python cli.py stop-bot
python cli.py uninstall-all
python cli.py show
```

Finding calendar URLs

- Use iCal/ICS URLs (not Google API URLs). The CLI only supports iCal feeds.
- During `setup`, the CLI can prompt you to add iCloud calendar iCal URLs.
- On My Mac calendars are not supported.
- Google Calendar: Settings for the calendar > Integrate calendar > copy “Secret address in iCal format”.
