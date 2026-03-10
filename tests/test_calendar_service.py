from __future__ import annotations

from datetime import date

from src.calendar.service import _normalize_ical_url, parse_ical_events


def test_parse_ical_events_filters_to_target_day():
    raw_ics = b"""BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
UID:1
DTSTAMP:20260309T010000Z
DTSTART:20260309T170000Z
DTEND:20260309T180000Z
SUMMARY:Design Review
DESCRIPTION:Review sprint scope
LOCATION:Zoom
END:VEVENT
BEGIN:VEVENT
UID:2
DTSTAMP:20260309T010000Z
DTSTART;VALUE=DATE:20260310
SUMMARY:Tomorrow Event
END:VEVENT
END:VCALENDAR
"""

    events = parse_ical_events(raw_ics, date(2026, 3, 9), "America/Los_Angeles")

    assert len(events) == 1
    assert events[0].title == "Design Review"
    assert events[0].location == "Zoom"


def test_parse_ical_events_supports_all_day_events():
    raw_ics = b"""BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
UID:3
DTSTAMP:20260309T010000Z
DTSTART;VALUE=DATE:20260309
DTEND;VALUE=DATE:20260310
SUMMARY:Company Offsite
END:VEVENT
END:VCALENDAR
"""

    events = parse_ical_events(raw_ics, date(2026, 3, 9), "UTC")

    assert len(events) == 1
    assert events[0].all_day is True


def test_normalize_ical_url_supports_webcal_scheme():
    assert _normalize_ical_url("webcal://example.com/a.ics") == "https://example.com/a.ics"
    assert _normalize_ical_url("webcals://example.com/a.ics") == "https://example.com/a.ics"
