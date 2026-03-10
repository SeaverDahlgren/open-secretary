from __future__ import annotations

import sys
from getpass import getpass


def prompt_required(label: str, default: str | None = None, secret: bool = False) -> str:
    while True:
        prompt = f"{label}"
        if default:
            prompt += f" [{default}]"
        prompt += ": "
        value = getpass(prompt) if secret else input(prompt)
        value = value.strip()
        if not value and default is not None:
            value = default
        if value:
            return value
        print("Value is required.", file=sys.stderr)


def prompt_optional(label: str, secret: bool = False) -> str | None:
    prompt = f"{label}: "
    value = getpass(prompt) if secret else input(prompt)
    value = value.strip()
    return value or None


def prompt_yes_no(label: str, default: bool = False) -> bool:
    default_label = "Y/n" if default else "y/N"
    while True:
        raw = input(f"{label} ({default_label}) ").strip().lower()
        if not raw:
            return default
        if raw in {"y", "yes"}:
            return True
        if raw in {"n", "no"}:
            return False
        print("Enter y or n.", file=sys.stderr)
