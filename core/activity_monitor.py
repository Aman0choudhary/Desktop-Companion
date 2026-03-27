from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from time import monotonic


@dataclass(slots=True)
class ActivitySnapshot:
    now: float
    idle_seconds: float
    recent_keypresses: int
    is_typing: bool


class ActivityMonitor:
    """Tracks lightweight activity signals.

    The current prototype is intentionally local and safe. It does not install
    global hooks; instead, the renderer can forward simulated activity into this
    monitor until we add a Windows-specific implementation behind the same API.
    """

    def __init__(self, typing_grace_seconds: float, typing_burst_threshold: int) -> None:
        now = monotonic()
        self._last_activity_at = now
        self._keypress_times: deque[float] = deque()
        self._typing_grace_seconds = typing_grace_seconds
        self._typing_burst_threshold = typing_burst_threshold

    def record_keyboard_activity(self, now: float | None = None) -> None:
        current = monotonic() if now is None else now
        self._last_activity_at = current
        self._keypress_times.append(current)
        self._trim(current)

    def record_presence(self, now: float | None = None) -> None:
        current = monotonic() if now is None else now
        self._last_activity_at = current
        self._trim(current)

    def snapshot(self, now: float | None = None) -> ActivitySnapshot:
        current = monotonic() if now is None else now
        self._trim(current)
        return ActivitySnapshot(
            now=current,
            idle_seconds=max(0.0, current - self._last_activity_at),
            recent_keypresses=len(self._keypress_times),
            is_typing=len(self._keypress_times) >= self._typing_burst_threshold,
        )

    def _trim(self, now: float) -> None:
        cutoff = now - self._typing_grace_seconds
        while self._keypress_times and self._keypress_times[0] < cutoff:
            self._keypress_times.popleft()
