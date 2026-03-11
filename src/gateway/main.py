from __future__ import annotations

import signal

from src.config import load_config
from src.gateway.service import TelegramGateway


def main() -> None:
    config = load_config()
    gateway = TelegramGateway(config)
    gateway.run()


def _handle_shutdown(signum: int, frame: object) -> None:
    raise KeyboardInterrupt


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, _handle_shutdown)
    main()
