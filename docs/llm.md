---
summary: "Gemini summarizer for daily agenda text"
read_when:
  - "When changing model selection or prompt formatting."
---

# LLM Package

Generates a concise daily summary from calendar events using Gemini.

- `build_summary_prompt` assembles the prompt with date, bullet style, and event details.
- `GeminiSummarizer` wraps `google.genai.Client` and defaults to `gemini-2.5-flash`.
- `summarize` calls `models.generate_content` and returns trimmed text or a fallback message.

Config

- `llm.model`
- `llm.api_key` or `GEMINI_API_KEY`
