from __future__ import annotations

import signal
import time

from src.config import load_config
from src.pipeline import DailySummaryPipeline
from src.scheduler import SummaryScheduler


def main() -> None:
    config = load_config()
    pipeline = DailySummaryPipeline(config)
    scheduler = SummaryScheduler(config, pipeline.run)
    scheduler.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        scheduler.shutdown()


def _handle_shutdown(signum: int, frame: object) -> None:
    raise KeyboardInterrupt


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, _handle_shutdown)
    main()
