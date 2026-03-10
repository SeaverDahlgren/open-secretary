from __future__ import annotations

from datetime import date

from google import genai

from src.shared import CalendarEvent


def build_summary_prompt(events: list[CalendarEvent], target_day: date) -> str:
    header = [
        "You are an assistant that creates concise daily plans.",
        f"Date: {target_day.isoformat()}",
        "Goal: summarize calendar items into an action-first agenda.",
        "Style: short bullets, include times, call out conflicts.",
        "If there are no events, return one bullet saying there are no scheduled tasks.",
        "",
        "Calendar events:",
    ]
    for event in events:
        if event.all_day:
            when = "All day"
        else:
            when = event.start.strftime("%H:%M")
        details = [f"- {when} | {event.title}"]
        if event.location:
            details.append(f"location={event.location}")
        if event.description:
            details.append(f"notes={event.description}")
        header.append(" ; ".join(details))
    return "\n".join(header)


class GeminiSummarizer:
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash") -> None:
        self.model = model
        self.client = genai.Client(api_key=api_key)

    def summarize(self, events: list[CalendarEvent], target_day: date) -> str:
        prompt = build_summary_prompt(events, target_day)
        response = self.client.models.generate_content(model=self.model, contents=prompt)
        text = (response.text or "").strip()
        return text or "No summary generated."
