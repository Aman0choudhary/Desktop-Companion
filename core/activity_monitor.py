from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from time import monotonic
from threading import Lock
from typing import Any


@dataclass(slots=True)
class ActivitySnapshot:
    now: float
    idle_seconds: float
    recent_keypresses: int
    is_typing: bool


@dataclass(slots=True)
class ActivityMonitorStatus:
    hooks_enabled: bool
    message: str


class ActivityMonitor:
    """Tracks desktop activity and can optionally attach global input hooks."""

    def __init__(self, typing_grace_seconds: float, typing_burst_threshold: int) -> None:
        now = monotonic()
        self._last_activity_at = now
        self._keypress_times: deque[float] = deque()
        self._typing_grace_seconds = typing_grace_seconds
        self._typing_burst_threshold = typing_burst_threshold
        self._lock = Lock()
        self._keyboard_listener: Any | None = None
        self._mouse_listener: Any | None = None
        self._hooks_enabled = False
        self._status_message = "Global activity hooks are not running."

    def record_keyboard_activity(self, now: float | None = None) -> None:
        current = monotonic() if now is None else now
        with self._lock:
            self._last_activity_at = current
            self._keypress_times.append(current)
            self._trim(current)

    def record_presence(self, now: float | None = None) -> None:
        current = monotonic() if now is None else now
        with self._lock:
            self._last_activity_at = current
            self._trim(current)

    def snapshot(self, now: float | None = None) -> ActivitySnapshot:
        current = monotonic() if now is None else now
        with self._lock:
            self._trim(current)
            return ActivitySnapshot(
                now=current,
                idle_seconds=max(0.0, current - self._last_activity_at),
                recent_keypresses=len(self._keypress_times),
                is_typing=len(self._keypress_times) >= self._typing_burst_threshold,
            )

    def start_global_hooks(self) -> ActivityMonitorStatus:
        if self._hooks_enabled:
            return self.status()

        try:
            from pynput import keyboard, mouse
        except Exception as exc:
            self._status_message = f"Global hooks unavailable: {exc}"
            return self.status()

        try:
            self._keyboard_listener = keyboard.Listener(on_press=self._on_key_press)
            self._mouse_listener = mouse.Listener(
                on_move=self._on_mouse_move,
                on_click=self._on_mouse_click,
                on_scroll=self._on_mouse_scroll,
            )
            self._keyboard_listener.daemon = True
            self._mouse_listener.daemon = True
            self._keyboard_listener.start()
            self._mouse_listener.start()
            self._hooks_enabled = True
            self._status_message = "Global keyboard and mouse activity hooks are running."
        except Exception as exc:
            self._hooks_enabled = False
            self._status_message = f"Failed to start global activity hooks: {exc}"
        return self.status()

    def stop(self) -> None:
        for listener in (self._keyboard_listener, self._mouse_listener):
            if listener is None:
                continue
            try:
                listener.stop()
            except Exception:
                pass
        self._keyboard_listener = None
        self._mouse_listener = None
        self._hooks_enabled = False
        if self._status_message == "Global keyboard and mouse activity hooks are running.":
            self._status_message = "Global activity hooks are not running."

    def status(self) -> ActivityMonitorStatus:
        return ActivityMonitorStatus(
            hooks_enabled=self._hooks_enabled,
            message=self._status_message,
        )

    def _on_key_press(self, _key: Any) -> None:
        self.record_keyboard_activity()

    def _on_mouse_move(self, _x: int, _y: int) -> None:
        self.record_presence()

    def _on_mouse_click(self, _x: int, _y: int, _button: Any, _pressed: bool) -> None:
        self.record_presence()

    def _on_mouse_scroll(self, _x: int, _y: int, _dx: int, _dy: int) -> None:
        self.record_presence()

    def _trim(self, now: float) -> None:
        cutoff = now - self._typing_grace_seconds
        while self._keypress_times and self._keypress_times[0] < cutoff:
            self._keypress_times.popleft()
