from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class MemoryState:
    synopsis: str = ""
    turns: list[dict[str, str]] = field(default_factory=list)


def load_memory(path: Path) -> MemoryState:
    if not path.exists():
        return MemoryState()
    text = path.read_text(encoding="utf-8")
    synopsis = _extract_section(text, "Synopsis").strip()
    turns = _extract_json_block(text) or []
    if not isinstance(turns, list):
        turns = []
    return MemoryState(synopsis=synopsis, turns=_sanitize_turns(turns))


def save_memory(path: Path, state: MemoryState) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = _render_memory(state)
    path.write_text(content, encoding="utf-8")


def append_turn(state: MemoryState, user_text: str, assistant_text: str) -> None:
    state.turns.append({"role": "user", "content": user_text})
    state.turns.append({"role": "assistant", "content": assistant_text})


def trim_turns(state: MemoryState, max_turns: int) -> None:
    if max_turns <= 0:
        state.turns = []
        return
    max_messages = max_turns * 2
    if len(state.turns) > max_messages:
        state.turns = state.turns[-max_messages:]


def turn_count(state: MemoryState) -> int:
    return len(state.turns) // 2


def _extract_section(text: str, heading: str) -> str:
    marker = f"## {heading}"
    if marker not in text:
        return ""
    after = text.split(marker, 1)[1]
    if "## " in after:
        after = after.split("## ", 1)[0]
    return after.strip()


def _extract_json_block(text: str) -> list[dict[str, str]] | None:
    start = "```json"
    end = "```"
    if start not in text:
        return None
    rest = text.split(start, 1)[1]
    if end not in rest:
        return None
    payload = rest.split(end, 1)[0]
    try:
        return json.loads(payload.strip())
    except json.JSONDecodeError:
        return None


def _sanitize_turns(turns: list[dict[str, str]]) -> list[dict[str, str]]:
    sanitized: list[dict[str, str]] = []
    for item in turns:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        content = item.get("content")
        if role not in {"user", "assistant"} or not isinstance(content, str):
            continue
        sanitized.append({"role": role, "content": content})
    return sanitized


def _render_memory(state: MemoryState) -> str:
    synopsis = state.synopsis.strip()
    turns_json = json.dumps(state.turns, indent=2, ensure_ascii=True)
    parts = [
        "# Agent Memory",
        "",
        "## Synopsis",
        synopsis or "(empty)",
        "",
        "## Turns",
        "```json",
        turns_json,
        "```",
        "",
    ]
    return "\n".join(parts)
