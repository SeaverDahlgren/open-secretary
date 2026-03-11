from __future__ import annotations

from datetime import date, datetime, time
from zoneinfo import ZoneInfo

import requests
from icalendar import Calendar

from src.shared import CalendarEvent


class CalendarService:
    def __init__(
        self,
        ical_urls: list[str],
        timezone: str = "UTC",
        timeout_s: int = 15,
    ) -> None:
        self.ical_urls = ical_urls
        self.timezone = timezone
        self.timeout_s = timeout_s

    def fetch_today_events(self, today: date | None = None) -> list[CalendarEvent]:
        target = today or datetime.now(ZoneInfo(self.timezone)).date()
        events: list[CalendarEvent] = []
        for url in self.ical_urls:
            response = requests.get(_normalize_ical_url(url), timeout=self.timeout_s)
            response.raise_for_status()
            events.extend(parse_ical_events(response.content, target, self.timezone))
        events.sort(key=lambda event: event.start)
        return events

    def fetch_events_for_range(self, start_day: date, end_day: date) -> list[CalendarEvent]:
        if end_day < start_day:
            raise ValueError("end_day must be >= start_day")
        tz = ZoneInfo(self.timezone)
        range_start = datetime.combine(start_day, time.min, tzinfo=tz)
        range_end = datetime.combine(end_day, time.max, tzinfo=tz)
        events: list[CalendarEvent] = []
        for url in self.ical_urls:
            response = requests.get(_normalize_ical_url(url), timeout=self.timeout_s)
            response.raise_for_status()
            events.extend(parse_ical_events_for_range(response.content, range_start, range_end, self.timezone))
        events.sort(key=lambda event: event.start)
        return events


def parse_ical_events(ical_content: bytes, target_day: date, timezone: str) -> list[CalendarEvent]:
    tz = ZoneInfo(timezone)
    calendar = Calendar.from_ical(ical_content)
    day_start = datetime.combine(target_day, time.min, tzinfo=tz)
    day_end = datetime.combine(target_day, time.max, tzinfo=tz)
    events: list[CalendarEvent] = []

    for component in calendar.walk("VEVENT"):
        dtstart = component.get("DTSTART")
        if not dtstart:
            continue

        start_value = dtstart.dt
        end_value = component.get("DTEND")
        end_dt_raw = end_value.dt if end_value else None

        all_day = isinstance(start_value, date) and not isinstance(start_value, datetime)

        if all_day:
            start_dt = datetime.combine(start_value, time.min, tzinfo=tz)
            if end_dt_raw and isinstance(end_dt_raw, date) and not isinstance(end_dt_raw, datetime):
                # iCal all-day DTEND is exclusive.
                end_dt = datetime.combine(end_dt_raw, time.min, tzinfo=tz)
            else:
                end_dt = datetime.combine(start_value, time.max, tzinfo=tz)
        else:
            start_dt = _to_tz(start_value, tz)
            end_dt = _to_tz(end_dt_raw, tz) if isinstance(end_dt_raw, datetime) else None

        if _intersects_day(start_dt, end_dt, day_start, day_end):
            events.append(
                CalendarEvent(
                    title=str(component.get("SUMMARY", "(No title)")),
                    start=start_dt,
                    end=end_dt,
                    all_day=all_day,
                    description=str(component.get("DESCRIPTION", "")),
                    location=str(component.get("LOCATION", "")),
                )
            )

    events.sort(key=lambda event: event.start)
    return events


def parse_ical_events_for_range(
    ical_content: bytes,
    range_start: datetime,
    range_end: datetime,
    timezone: str,
) -> list[CalendarEvent]:
    tz = ZoneInfo(timezone)
    if range_start.tzinfo is None:
        range_start = range_start.replace(tzinfo=tz)
    if range_end.tzinfo is None:
        range_end = range_end.replace(tzinfo=tz)
    calendar = Calendar.from_ical(ical_content)
    events: list[CalendarEvent] = []

    for component in calendar.walk("VEVENT"):
        dtstart = component.get("DTSTART")
        if not dtstart:
            continue

        start_value = dtstart.dt
        end_value = component.get("DTEND")
        end_dt_raw = end_value.dt if end_value else None

        all_day = isinstance(start_value, date) and not isinstance(start_value, datetime)

        if all_day:
            start_dt = datetime.combine(start_value, time.min, tzinfo=tz)
            if end_dt_raw and isinstance(end_dt_raw, date) and not isinstance(end_dt_raw, datetime):
                end_dt = datetime.combine(end_dt_raw, time.min, tzinfo=tz)
            else:
                end_dt = datetime.combine(start_value, time.max, tzinfo=tz)
        else:
            start_dt = _to_tz(start_value, tz)
            end_dt = _to_tz(end_dt_raw, tz) if isinstance(end_dt_raw, datetime) else None

        if _intersects_range(start_dt, end_dt, range_start, range_end):
            events.append(
                CalendarEvent(
                    title=str(component.get("SUMMARY", "(No title)")),
                    start=start_dt,
                    end=end_dt,
                    all_day=all_day,
                    description=str(component.get("DESCRIPTION", "")),
                    location=str(component.get("LOCATION", "")),
                )
            )

    events.sort(key=lambda event: event.start)
    return events


def _intersects_day(
    start_dt: datetime,
    end_dt: datetime | None,
    day_start: datetime,
    day_end: datetime,
) -> bool:
    end = end_dt or start_dt
    return start_dt <= day_end and end >= day_start


def _intersects_range(
    start_dt: datetime,
    end_dt: datetime | None,
    range_start: datetime,
    range_end: datetime,
) -> bool:
    end = end_dt or start_dt
    return start_dt <= range_end and end >= range_start


def _to_tz(value: datetime, tz: ZoneInfo) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=tz)
    return value.astimezone(tz)


def _normalize_ical_url(url: str) -> str:
    if url.startswith("webcal://"):
        return "https://" + url[len("webcal://") :]
    if url.startswith("webcals://"):
        return "https://" + url[len("webcals://") :]
    return url
