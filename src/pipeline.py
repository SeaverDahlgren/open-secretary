from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from src.calendar import CalendarService
from src.config import AppConfig
from src.llm import GeminiSummarizer
from src.messenger import TelegramMessenger


class DailySummaryPipeline:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.calendar = CalendarService(
            ical_urls=config.calendar.ical_urls,
            timezone=config.schedule.timezone,
        )
        self.summarizer = GeminiSummarizer(
            api_key=config.llm.api_key,
            model=config.llm.model,
        )
        self.messenger = TelegramMessenger(
            bot_token=config.messenger.telegram_bot_token,
            chat_id=config.messenger.telegram_chat_id,
        )

    def run(self) -> str:
        target_day = datetime.now(ZoneInfo(self.config.schedule.timezone)).date()
        events = self.calendar.fetch_today_events(target_day)
        summary = self.summarizer.summarize(events, target_day)
        return self.messenger.send(summary)
