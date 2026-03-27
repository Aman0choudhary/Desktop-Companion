from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np


@dataclass(slots=True)
class WakeWordStatus:
    available: bool
    message: str
    model_name: str


class WakeWordDetector:
    def __init__(
        self,
        model_name: str,
        threshold: float,
        models_dir: str | Path,
        custom_model_path: str | Path | None = None,
    ) -> None:
        self.model_name = model_name
        self.threshold = threshold
        self.models_dir = Path(models_dir)
        self.custom_model_path = Path(custom_model_path) if custom_model_path else None
        self.model: Any | None = None
        self._prediction_key = model_name
        self._status = WakeWordStatus(
            available=False,
            message="Wake-word detector not initialized.",
            model_name=model_name,
        )

    def initialize(self) -> WakeWordStatus:
        model_path = self._resolve_model_path()
        if not model_path.exists():
            self._status = WakeWordStatus(
                available=False,
                message=f"Wake-word model is missing: {model_path}",
                model_name=self.model_name,
            )
            return self._status

        try:
            from openwakeword.model import Model

            self.model = Model(
                wakeword_models=[str(model_path)],
                inference_framework="onnx",
                melspec_model_path=str(self.models_dir / "melspectrogram.onnx"),
                embedding_model_path=str(self.models_dir / "embedding_model.onnx"),
            )
            self._prediction_key = model_path.stem.replace("_v0.1", "")
            self._status = WakeWordStatus(
                available=True,
                message=f"Wake-word detector ready with model '{self._prediction_key}'.",
                model_name=self._prediction_key,
            )
        except Exception as exc:
            self.model = None
            self._status = WakeWordStatus(
                available=False,
                message=f"Wake-word detector failed to initialize: {exc}",
                model_name=self.model_name,
            )
        return self._status

    def process_chunk(self, chunk: np.ndarray) -> bool:
        if self.model is None:
            return False
        predictions = self.model.predict(
            chunk,
            threshold={self._prediction_key: self.threshold},
            debounce_time=1.0,
        )
        if self._prediction_key in predictions:
            return float(predictions.get(self._prediction_key, 0.0)) >= self.threshold
        return max((float(score) for score in predictions.values()), default=0.0) >= self.threshold

    def reset(self) -> None:
        if self.model is not None:
            self.model.reset()

    def status(self) -> WakeWordStatus:
        return self._status

    def _resolve_model_path(self) -> Path:
        if self.custom_model_path is not None:
            return self.custom_model_path
        return self.models_dir / f"{self.model_name}_v0.1.onnx"
