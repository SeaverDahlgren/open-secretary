from __future__ import annotations

from collections.abc import Callable

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from src.config import AppConfig


class SummaryScheduler:
    def __init__(self, config: AppConfig, job_fn: Callable[[], None]) -> None:
        self.config = config
        self.job_fn = job_fn
        self.scheduler = BackgroundScheduler(timezone=config.schedule.timezone)

    def configure(self) -> None:
        hour_str, minute_str = self.config.schedule.time.split(":")
        trigger = CronTrigger(
            day_of_week=",".join(self.config.schedule.days),
            hour=int(hour_str),
            minute=int(minute_str),
            timezone=self.config.schedule.timezone,
        )
        self.scheduler.add_job(self.job_fn, trigger=trigger, id="daily_summary", replace_existing=True)

    def start(self) -> None:
        self.configure()
        self.scheduler.start()

    def shutdown(self) -> None:
        self.scheduler.shutdown(wait=False)
