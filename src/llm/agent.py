from __future__ import annotations

from google import genai

from src.gateway.memory import MemoryState


class AgentResponder:
    def __init__(self, api_key: str, model: str, system_prompt: str, max_reply_words: int) -> None:
        self.model = model
        self.system_prompt = system_prompt
        self.max_reply_words = max_reply_words
        self.client = genai.Client(api_key=api_key)

    def respond(self, user_text: str, memory: MemoryState) -> str:
        prompt = self._build_chat_prompt(user_text, memory)
        response = self.client.models.generate_content(model=self.model, contents=prompt)
        text = (response.text or "").strip()
        return _truncate_words(text or "No response generated.", self.max_reply_words)

    def summarize_memory(self, memory: MemoryState) -> str:
        prompt = self._build_summary_prompt(memory)
        response = self.client.models.generate_content(model=self.model, contents=prompt)
        text = (response.text or "").strip()
        return text or memory.synopsis

    def _build_chat_prompt(self, user_text: str, memory: MemoryState) -> str:
        lines = [
            self.system_prompt,
            "",
            "Context synopsis:",
            memory.synopsis.strip() or "(none)",
            "",
            "Recent conversation:",
        ]
        for item in memory.turns:
            role = item.get("role", "user")
            content = item.get("content", "")
            lines.append(f"{role}: {content}")
        lines.extend(["", f"user: {user_text}", "assistant:"])
        return "\n".join(lines)

    def _build_summary_prompt(self, memory: MemoryState) -> str:
        lines = [
            "Summarize the conversation for long-term memory.",
            "Keep it short, factual, and focused on user preferences, plans, and open threads.",
            "",
            "Existing synopsis:",
            memory.synopsis.strip() or "(none)",
            "",
            "Recent conversation:",
        ]
        for item in memory.turns:
            role = item.get("role", "user")
            content = item.get("content", "")
            lines.append(f"{role}: {content}")
        lines.append("")
        return "\n".join(lines)


def _truncate_words(text: str, max_words: int) -> str:
    if max_words <= 0:
        return ""
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]).rstrip() + "…"
