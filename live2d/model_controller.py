from __future__ import annotations

from pathlib import Path


class ModelController:
    """Placeholder for the future Live2D integration layer."""

    def __init__(self, model_path: str | None = None) -> None:
        self.model_path = Path(model_path) if model_path else None

    def has_model(self) -> bool:
        return bool(self.model_path and self.model_path.exists())
