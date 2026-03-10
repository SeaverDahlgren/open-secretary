---
summary: "Schedules the daily summary job with APScheduler"
read_when:
  - "When changing scheduling logic"
---

# Scheduler Package

Runs the daily summary on a cron schedule using APScheduler.

- `SummaryScheduler` wraps `BackgroundScheduler` with a timezone from config.
- `configure` builds a `CronTrigger` from `schedule.time`, `schedule.days`, `schedule.timezone`.
- Job id is `daily_summary` with `replace_existing=True` to avoid duplicates.
- `start` configures and starts the scheduler; `shutdown` stops it without waiting.
