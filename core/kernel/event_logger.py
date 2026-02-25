from typing import Callable

from .types import ErrorEvent, ProcessingStats


class EventLogger:
    def __init__(self, callback: Callable[[str], None], mode_name: str):
        self._callback = callback
        self._mode_name = mode_name

    def info(self, message: str) -> None:
        self._callback(message)

    def error(self, stats: ProcessingStats, event: ErrorEvent) -> None:
        stats.add_error(event)
        self._callback(f"[{self._mode_name}] {event.as_log_line()}")

