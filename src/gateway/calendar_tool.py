from __future__ import annotations

import re
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from dateutil import parser as date_parser

from src.calendar import CalendarService
from src.shared import CalendarEvent

WEEKDAYS = {
    "mon": 0,
    "monday": 0,
    "tue": 1,
    "tues": 1,
    "tuesday": 1,
    "wed": 2,
    "weds": 2,
    "wednesday": 2,
    "thu": 3,
    "thurs": 3,
    "thursday": 3,
    "fri": 4,
    "friday": 4,
    "sat": 5,
    "saturday": 5,
    "sun": 6,
    "sunday": 6,
}


@dataclass(slots=True)
class CalendarWindow:
    start: date
    end: date


class CalendarTool:
    def __init__(
        self,
        ical_urls: list[str],
        timezone: str,
        max_days: int = 30,
        cache_ttl_s: int = 600,
    ) -> None:
        self.service = CalendarService(ical_urls=ical_urls, timezone=timezone)
        self.tz = ZoneInfo(timezone)
        self.max_days = max_days
        self.cache_ttl_s = cache_ttl_s
        self._cache: dict[date, tuple[float, list[CalendarEvent]]] = {}

    def get_context(self, user_text: str) -> str | None:
        if not is_calendar_query(user_text):
            return None
        today = datetime.now(self.tz).date()
        window = extract_date_window(user_text, today, self.max_days)
        events_by_day = self._fetch_window(window)
        return render_calendar_context(window, events_by_day)

    def _fetch_window(self, window: CalendarWindow) -> dict[date, list[CalendarEvent]]:
        missing = [d for d in _iter_days(window.start, window.end) if not self._is_cached(d)]
        if missing:
            events = self.service.fetch_events_for_range(window.start, window.end)
            self._populate_cache(window, events)
        return {day: self._cache[day][1] for day in _iter_days(window.start, window.end)}

    def _is_cached(self, day: date) -> bool:
        entry = self._cache.get(day)
        if not entry:
            return False
        ts, _ = entry
        return (time.time() - ts) <= self.cache_ttl_s

    def _populate_cache(self, window: CalendarWindow, events: list[CalendarEvent]) -> None:
        now = time.time()
        for day in _iter_days(window.start, window.end):
            day_events = [event for event in events if _event_intersects_day(event, day, self.tz)]
            self._cache[day] = (now, day_events)


def is_calendar_query(text: str) -> bool:
    lowered = text.lower()
    keywords = [
        "calendar",
        "schedule",
        "meeting",
        "meetings",
        "event",
        "events",
        "agenda",
        "availability",
        "available",
        "free",
        "busy",
        "conflict",
        "today",
        "tomorrow",
        "next week",
        "this week",
        "next month",
        "next",
    ]
    if any(keyword in lowered for keyword in keywords):
        return True
    return any(word in lowered for word in WEEKDAYS)


def extract_date_window(text: str, today: date, max_days: int) -> CalendarWindow:
    lowered = text.lower()

    if "today" in lowered:
        return CalendarWindow(today, today)
    if "tomorrow" in lowered:
        day = today + timedelta(days=1)
        return CalendarWindow(day, day)

    match = re.search(r"\bnext\s+(\d{1,2})\s+days\b", lowered)
    if match:
        days = min(int(match.group(1)), max_days)
        return CalendarWindow(today, today + timedelta(days=days - 1))

    if "next week" in lowered or "this week" in lowered:
        return CalendarWindow(today, min(today + timedelta(days=6), today + timedelta(days=max_days - 1)))

    if "next month" in lowered:
        return CalendarWindow(today, today + timedelta(days=max_days - 1))

    for word, weekday in WEEKDAYS.items():
        if re.search(rf"\b{re.escape(word)}\b", lowered):
            target = _next_weekday(today, weekday)
            return CalendarWindow(target, target)

    explicit = _extract_explicit_date(lowered)
    if explicit:
        return CalendarWindow(explicit, explicit)

    return CalendarWindow(today, today)


def render_calendar_context(
    window: CalendarWindow,
    events_by_day: dict[date, list[CalendarEvent]],
    max_events: int = 50,
) -> str:
    days = list(_iter_days(window.start, window.end))
    total_events = sum(len(events_by_day.get(day, [])) for day in days)
    header = f"Calendar events ({window.start.isoformat()} to {window.end.isoformat()}):"
    if total_events == 0:
        return f"{header}\n- No events found."

    lines = [header]
    count = 0
    for day in days:
        events = events_by_day.get(day, [])
        if not events:
            continue
        lines.append(day.isoformat() + ":")
        for event in sorted(events, key=lambda e: e.start):
            if count >= max_events:
                remaining = total_events - max_events
                lines.append(f"- …and {remaining} more")
                return "\n".join(lines)
            lines.append(_format_event(event))
            count += 1
    return "\n".join(lines)


def _format_event(event: CalendarEvent) -> str:
    if event.all_day:
        when = "All day"
    else:
        when = event.start.strftime("%H:%M")
    title = event.title
    if event.location:
        title = f"{title} ({event.location})"
    return f"- {when} | {title}"


def _iter_days(start: date, end: date):
    current = start
    while current <= end:
        yield current
        current = current + timedelta(days=1)


def _next_weekday(today: date, weekday: int) -> date:
    delta = (weekday - today.weekday()) % 7
    if delta == 0:
        return today
    return today + timedelta(days=delta)


def _extract_explicit_date(text: str) -> date | None:
    for pattern in [r"\b\d{4}-\d{2}-\d{2}\b", r"\b\d{1,2}/\d{1,2}/\d{2,4}\b", r"\b\d{1,2}/\d{1,2}\b"]:
        match = re.search(pattern, text)
        if match:
            try:
                parsed = date_parser.parse(match.group(0), default=datetime.now())
                return parsed.date()
            except (ValueError, OverflowError):
                return None
    return None


def _event_intersects_day(event: CalendarEvent, day: date, tz: ZoneInfo) -> bool:
    day_start = datetime.combine(day, datetime.min.time(), tzinfo=tz)
    day_end = datetime.combine(day, datetime.max.time(), tzinfo=tz)
    end = event.end or event.start
    return event.start <= day_end and end >= day_start
