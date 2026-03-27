from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile

import numpy as np
import soundfile as sf


@dataclass(slots=True)
class SpeechToTextStatus:
    ready: bool
    message: str


class SpeechToTextService:
    def __init__(self, model_size: str, compute_type: str, download_root: str | Path) -> None:
        self.model_size = model_size
        self.compute_type = compute_type
        self.download_root = Path(download_root)
        self.download_root.mkdir(parents=True, exist_ok=True)
        self._model = None

    def status(self) -> SpeechToTextStatus:
        if self._model is None:
            return SpeechToTextStatus(
                ready=False,
                message=f"Whisper model '{self.model_size}' is not loaded yet.",
            )
        return SpeechToTextStatus(
            ready=True,
            message=f"Whisper model '{self.model_size}' is loaded.",
        )

    def transcribe_pcm16(self, audio: np.ndarray, sample_rate_hz: int) -> str:
        model = self._ensure_model()
        with NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_path = Path(temp_file.name)
        try:
            sf.write(temp_path, audio, sample_rate_hz, subtype="PCM_16")
            segments, _info = model.transcribe(str(temp_path), language="en", vad_filter=True)
            text = " ".join(segment.text.strip() for segment in segments).strip()
            return text
        finally:
            temp_path.unlink(missing_ok=True)

    def _ensure_model(self):
        if self._model is None:
            from faster_whisper import WhisperModel

            self._model = WhisperModel(
                self.model_size,
                compute_type=self.compute_type,
                download_root=str(self.download_root),
            )
        return self._model
