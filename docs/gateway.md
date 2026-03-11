---
summary: "Telegram polling gateway for agent chat"
read_when:
  - "When changing Telegram polling or agent chat behavior"
---

# Gateway Package

Polls Telegram for new messages and forwards them to the LLM agent.

- Uses `getUpdates` polling with configurable interval/timeout.
- Ignores messages older than startup by advancing offset.
- Filters to the configured `telegram_chat_id`.
- Stores memory in a local markdown file with synopsis + last turns.

Config (`agent`)

- `enabled`
- `memory_path`
- `memory_max_turns`
- `system_prompt`
- `max_reply_words`
- `poll_interval_s`
- `poll_timeout_s`
- `synopsis_every_n_turns`

Run

```bash
python -m src.gateway.main
```

Install as a service (macOS)

```bash
python cli.py install-gateway
python cli.py gateway-status
python cli.py uninstall-gateway
```
