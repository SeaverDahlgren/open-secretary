from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

from src.llm import build_summary_prompt
from src.shared import CalendarEvent


def test_build_summary_prompt_includes_event_details():
    event = CalendarEvent(
        title="Sprint Planning",
        start=datetime(2026, 3, 9, 10, 0, tzinfo=ZoneInfo("UTC")),
        end=None,
        all_day=False,
        description="Bring backlog priorities",
        location="Room A",
    )

    prompt = build_summary_prompt([event], date(2026, 3, 9))

    assert "Sprint Planning" in prompt
    assert "10:00" in prompt
    assert "location=Room A" in prompt
