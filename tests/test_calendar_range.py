from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from src.calendar.service import parse_ical_events_for_range


def test_parse_ical_events_for_range_filters_to_window():
    raw_ics = b"""BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
UID:1
DTSTAMP:20260309T010000Z
DTSTART:20260309T170000Z
DTEND:20260309T180000Z
SUMMARY:Design Review
END:VEVENT
BEGIN:VEVENT
UID:2
DTSTAMP:20260309T010000Z
DTSTART:20260312T170000Z
DTEND:20260312T180000Z
SUMMARY:Later Event
END:VEVENT
END:VCALENDAR
"""

    tz = ZoneInfo("UTC")
    range_start = datetime(2026, 3, 9, 0, 0, tzinfo=tz)
    range_end = datetime(2026, 3, 10, 23, 59, tzinfo=tz)

    events = parse_ical_events_for_range(raw_ics, range_start, range_end, "UTC")

    assert len(events) == 1
    assert events[0].title == "Design Review"
