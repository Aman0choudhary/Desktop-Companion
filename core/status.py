from __future__ import annotations

from dataclasses import dataclass
from threading import Lock


@dataclass(slots=True)
class AppStatusSnapshot:
    dnd_enabled: bool = False
    voice_enabled: bool = False
    click_through_enabled: bool = True
    autostart_enabled: bool = False
    active_model_name: str = "None"


class AppStatusStore:
    def __init__(self) -> None:
        self._lock = Lock()
        self._snapshot = AppStatusSnapshot()

    def update(self, **changes: object) -> None:
        with self._lock:
            for key, value in changes.items():
                if hasattr(self._snapshot, key):
                    setattr(self._snapshot, key, value)

    def snapshot(self) -> AppStatusSnapshot:
        with self._lock:
            return AppStatusSnapshot(
                dnd_enabled=self._snapshot.dnd_enabled,
                voice_enabled=self._snapshot.voice_enabled,
                click_through_enabled=self._snapshot.click_through_enabled,
                autostart_enabled=self._snapshot.autostart_enabled,
                active_model_name=self._snapshot.active_model_name,
            )
