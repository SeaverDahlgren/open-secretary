from __future__ import annotations

from src.config import AppConfig, CalendarConfig, LLMConfig, MessengerConfig, ScheduleConfig
from src.scheduler import SummaryScheduler


def _config() -> AppConfig:
    return AppConfig(
        schedule=ScheduleConfig(time="08:15", days=["mon", "wed", "fri"], timezone="UTC"),
        calendar=CalendarConfig(ical_urls=["https://example.com/a.ics"]),
        llm=LLMConfig(model="gemini-2.0-flash", api_key="k"),
        messenger=MessengerConfig(
            telegram_bot_token="token",
            telegram_chat_id="12345",
        ),
    )


def test_scheduler_creates_single_daily_summary_job():
    scheduler = SummaryScheduler(_config(), lambda: None)

    scheduler.start()

    jobs = scheduler.scheduler.get_jobs()
    assert len(jobs) == 1
    assert jobs[0].id == "daily_summary"
    assert str(jobs[0].trigger).startswith("cron[")
    scheduler.shutdown()
