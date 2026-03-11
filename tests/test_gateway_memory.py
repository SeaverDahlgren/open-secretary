from __future__ import annotations

from pathlib import Path

from src.gateway.memory import MemoryState, append_turn, load_memory, save_memory, trim_turns, turn_count


def test_memory_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "agent_memory.md"
    state = MemoryState(synopsis="User prefers mornings.")
    append_turn(state, "Hi", "Hello")
    append_turn(state, "Plan my day", "Drafting a plan.")
    trim_turns(state, max_turns=1)
    save_memory(path, state)

    loaded = load_memory(path)
    assert loaded.synopsis == "User prefers mornings."
    assert turn_count(loaded) == 1
    assert loaded.turns[0]["role"] == "user"
