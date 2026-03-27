from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import json


@dataclass(slots=True)
class AppConfig:
    window_width: int = 220
    window_height: int = 220
    update_interval_ms: int = 33
    click_through_window: bool = True
    use_global_activity_hooks: bool = True
    enable_voice_pipeline: bool = True
    wake_word_phrase: str = "Hey Nezuko"
    wake_word_model_name: str = "hey_jarvis"
    wake_word_model_path: str = ""
    wake_word_threshold: float = 0.5
    voice_sample_rate_hz: int = 16000
    voice_chunk_size: int = 1280
    voice_capture_max_seconds: float = 8.0
    voice_end_silence_seconds: float = 1.2
    voice_rms_silence_threshold: float = 0.012
    whisper_model_size: str = "tiny.en"
    whisper_compute_type: str = "int8"
    edge_tts_voice: str = "en-IN-NeerjaNeural"
    live2d_model_path: str = ""
    roam_speed_px_per_second: float = 180.0
    screen_margin: int = 40
    min_pause_seconds: float = 1.2
    max_pause_seconds: float = 3.5
    greeting_duration_seconds: float = 4.0
    hype_duration_seconds: float = 3.0
    sleep_after_seconds: float = 20.0
    typing_grace_seconds: float = 3.0
    typing_burst_threshold: int = 3
    bubble_duration_seconds: float = 4.0


DEFAULT_CONFIG = AppConfig()


def config_root() -> Path:
    return Path(__file__).resolve().parent.parent


def settings_path() -> Path:
    return config_root() / "assets" / "settings.json"


def load_app_config() -> AppConfig:
    config = AppConfig()
    path = settings_path()
    if not path.exists():
        return config

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return config

    for field_name in asdict(config).keys():
        if field_name in data:
            setattr(config, field_name, data[field_name])
    return config


def save_app_config(config: AppConfig) -> None:
    path = settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(config), indent=2), encoding="utf-8")
