DEFAULT_SCHEDULE_TIME = "08:00"
DEFAULT_SCHEDULE_DAYS = "mon,tue,wed,thu,fri"
DEFAULT_TIMEZONE = "UTC"
DEFAULT_MODEL = "gemini-2.5-flash"

TIMEZONE_OPTIONS = [
    "UTC",
    "America/Los_Angeles",
    "America/Denver",
    "America/Chicago",
    "America/New_York",
    "Europe/London",
    "Europe/Paris",
    "Europe/Berlin",
    "Asia/Tokyo",
    "Asia/Shanghai",
    "Asia/Singapore",
    "Australia/Sydney",
]

SENSITIVE_PATHS: set[tuple[str, str]] = {
    ("llm", "api_key"),
    ("messenger", "telegram_bot_token"),
}
