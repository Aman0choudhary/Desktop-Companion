from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class AppConfig:
    window_width: int = 220
    window_height: int = 220
    update_interval_ms: int = 33
    roam_speed_px_per_second: float = 180.0
    screen_margin: int = 40
    min_pause_seconds: float = 1.2
    max_pause_seconds: float = 3.5
    greeting_duration_seconds: float = 4.0
    sleep_after_seconds: float = 20.0
    typing_grace_seconds: float = 3.0
    typing_burst_threshold: int = 3
    bubble_duration_seconds: float = 4.0


DEFAULT_CONFIG = AppConfig()
