from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(slots=True)
class CalendarEvent:
    title: str
    start: datetime
    end: Optional[datetime]
    all_day: bool
    description: str = ""
    location: str = ""
