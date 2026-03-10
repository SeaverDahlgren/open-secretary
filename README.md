# openSecretary

Daily calendar summary to Telegram using APScheduler + iCal + Gemini.

Packages

- `src/calendar`: fetches iCal data and maps it to `CalendarEvent` items.
- `src/cli`: manages config.json interactively or via commands.
- `src/llm`: builds prompts and calls Gemini to generate the summary.
- `src/messenger`: sends the summary to Telegram.
- `src/scheduler`: schedules the daily job with APScheduler.
- `src/shared`: shared data models such as `CalendarEvent`.
