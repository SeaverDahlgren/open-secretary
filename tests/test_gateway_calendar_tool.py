from __future__ import annotations

from datetime import date

from src.gateway.calendar_tool import CalendarWindow, _parse_llm_window, extract_date_window, is_calendar_query


def test_is_calendar_query_matches_keywords():
    assert is_calendar_query("What is on my calendar today?")
    assert is_calendar_query("Any meetings next week?")
    assert is_calendar_query("Do I have anything Tuesday?")


def test_extract_date_window_today():
    today = date(2026, 3, 11)
    window = extract_date_window("today", today, max_days=30)
    assert window == CalendarWindow(today, today)


def test_extract_date_window_next_days():
    today = date(2026, 3, 11)
    window = extract_date_window("next 3 days", today, max_days=30)
    assert window.start == today
    assert window.end == date(2026, 3, 13)


def test_parse_llm_window_clamps_to_max_days():
    today = date(2026, 3, 11)
    text = '{"start_date":"2026-03-11","end_date":"2026-04-30"}'
    window = _parse_llm_window(text, today, max_days=30)
    assert window is not None
    assert window.start == date(2026, 3, 11)
    assert window.end == date(2026, 4, 9)
