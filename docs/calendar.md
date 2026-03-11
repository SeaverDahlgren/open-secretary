---
summary: "Fetches and parses iCal events into CalendarEvent items"
read_when:
  - "Changing calendar interface logic"
---

# Calendar Package

Fetches iCal data and returns a timezone-aware list of events for a target day.

- `CalendarService.fetch_today_events` loads each iCal URL via `requests` and merges events for the target date.
- `parse_ical_events` converts VEVENTs into `CalendarEvent` items and sorts by start time.
- All-day events and exclusive `DTEND` handling follow iCal semantics.
- `webcal://` and `webcals://` URLs are normalized to `https://`.

Behavior notes

- Filters events to those intersecting the target day in the configured timezone.
- Naive datetimes are treated as being in the configured timezone.
- RRULE recurrence expansion is not implemented.
