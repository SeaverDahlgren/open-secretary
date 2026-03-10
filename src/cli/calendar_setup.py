from __future__ import annotations

from .prompts import prompt_optional, prompt_required, prompt_yes_no

ICLOUD_ICAL_HELP = [
    "iCloud Calendar: iCloud.com > Calendar > Share (or Calendar settings).",
    "Copy the iCal/ICS URL for each calendar you want to share.",
]

GOOGLE_ICAL_HELP = [
    "Google Calendar: Settings for the calendar > Integrate calendar.",
    "Copy \"Secret address in iCal format\".",
]


def prompt_ical_urls() -> list[str]:
    urls: list[str] = []

    if prompt_yes_no("Add iCloud Calendar URLs?"):
        print("iCloud iCal help:")
        for line in ICLOUD_ICAL_HELP:
            print(f"- {line}")
        urls.extend(_prompt_additional_urls("iCloud Calendar iCal URL"))

    if prompt_yes_no("Add Google Calendar(s)?"):
        print("Google iCal help:")
        for line in GOOGLE_ICAL_HELP:
            print(f"- {line}")
        urls.extend(_prompt_additional_urls("Google Calendar iCal URL"))

    if not urls:
        print("At least one iCal URL is required.")
        urls.extend(_prompt_additional_urls("Calendar iCal URL"))

    return urls


def _prompt_additional_urls(label: str) -> list[str]:
    urls: list[str] = []
    first = prompt_required(label)
    urls.append(first)
    while True:
        more = prompt_optional("Add another iCal URL? (y/N)") or "n"
        if more.lower() not in {"y", "yes"}:
            break
        extra = prompt_required("Additional iCal URL")
        urls.append(extra)
    return urls

