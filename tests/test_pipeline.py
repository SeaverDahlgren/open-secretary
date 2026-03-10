from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from src.config import AppConfig, CalendarConfig, LLMConfig, MessengerConfig, ScheduleConfig
from src.pipeline import DailySummaryPipeline
from src.shared import CalendarEvent


class FakeCalendar:
    def fetch_today_events(self, day):
        return [
            CalendarEvent(
                title="Standup",
                start=datetime(2026, 3, 9, 9, 0, tzinfo=ZoneInfo("UTC")),
                end=None,
                all_day=False,
            )
        ]


class FakeLLM:
    def summarize(self, events, day):
        return "- 09:00 Standup"


class FakeMessenger:
    def send(self, message: str):
        assert "Standup" in message
        return "SM123"


def test_pipeline_runs_end_to_end():
    cfg = AppConfig(
        schedule=ScheduleConfig(time="08:15", days=["mon"], timezone="UTC"),
        calendar=CalendarConfig(ical_urls=["https://example.com"]),
        llm=LLMConfig(model="gemini-2.0-flash", api_key="k"),
        messenger=MessengerConfig(
            telegram_bot_token="token",
            telegram_chat_id="12345",
        ),
    )

    pipeline = DailySummaryPipeline(cfg)
    pipeline.calendar = FakeCalendar()
    pipeline.summarizer = FakeLLM()
    pipeline.messenger = FakeMessenger()

    sid = pipeline.run()

    assert sid == "SM123"
