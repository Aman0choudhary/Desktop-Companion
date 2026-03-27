from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from core.state_machine import NezukoState


@dataclass(slots=True)
class ModelStatus:
    available: bool
    loaded: bool
    message: str


class ModelController:
    def __init__(self, model_path: str | Path | None = None) -> None:
        self.model_path = self.resolve_model_path(model_path) if model_path else self.find_default_model_path()
        self.runtime: Any | None = None
        self.model: Any | None = None
        self.motion_groups: dict[str, int] = {}
        self.expression_ids: list[str] = []
        self._current_state: NezukoState | None = None
        self._initialized = False

    @staticmethod
    def find_default_model_path(root: str | Path | None = None) -> Path | None:
        base = Path(root) if root else Path.cwd()
        candidates = [
            base / "assets" / "live2d",
            base / "rendering" / "assets",
            base / "live2d" / "assets",
        ]
        for candidate_dir in candidates:
            if not candidate_dir.exists():
                continue
            matches = sorted(candidate_dir.rglob("*.model3.json"))
            if matches:
                return matches[0]
        return None

    @staticmethod
    def resolve_model_path(model_path: str | Path | None) -> Path | None:
        if model_path is None:
            return None
        path = Path(model_path)
        if path.is_dir():
            matches = sorted(path.rglob("*.model3.json"))
            return matches[0] if matches else None
        return path

    def status(self) -> ModelStatus:
        if self.model_path is None:
            return ModelStatus(False, False, "No Live2D model found. Place a .model3.json file in assets/live2d/.")
        if not self.model_path.exists():
            return ModelStatus(False, False, f"Configured Live2D model path is missing: {self.model_path}")
        if self.model is None:
            return ModelStatus(True, False, f"Live2D model discovered at {self.model_path.name}.")
        return ModelStatus(True, True, f"Live2D model loaded: {self.model_path.name}.")

    def supports_live2d(self) -> bool:
        return self.model_path is not None and self.model_path.exists()

    def model_name(self) -> str:
        if self.model_path is None:
            return "None"
        return self.model_path.stem.replace(".model3", "")

    def initialize(self, width: int, height: int) -> ModelStatus:
        if self.model_path is None or not self.model_path.exists():
            return self.status()
        if self._initialized:
            return self.status()

        import live2d.v3 as live2d_v3

        self.runtime = live2d_v3
        self.runtime.init()
        self.runtime.glInit()
        self.model = self.runtime.LAppModel()
        self.model.LoadModelJson(str(self.model_path))
        self.model.Resize(width, height)
        self.model.SetAutoBlinkEnable(True)
        self.model.SetAutoBreathEnable(True)
        self.model.SetScale(2.6)
        self.model.SetOffset(0.0, -0.28)
        self.motion_groups = dict(self.model.GetMotionGroups() or {})
        self.expression_ids = list(self.model.GetExpressionIds() or [])
        self._initialized = True
        return self.status()

    def resize(self, width: int, height: int) -> None:
        if self.model is not None:
            self.model.Resize(width, height)

    def update_for_pose(self, *, state: NezukoState, facing_right: bool, bob_offset: float, opacity: float) -> None:
        if self.model is None:
            return

        self.apply_state(state)
        params = self.runtime.StandardParams
        angle_x = 10.0 if facing_right else -10.0
        self.model.SetParameterValue(params.ParamAngleX, angle_x)
        self.model.SetParameterValue(params.ParamBodyAngleX, angle_x * 0.35)
        self.model.SetParameterValue(params.ParamBreath, min(1.0, max(0.0, 0.5 + (bob_offset / 12.0))))
        mouth_open = {
            NezukoState.SLEEPING: 0.0,
            NezukoState.DND: 0.0,
            NezukoState.WORK: 0.08,
            NezukoState.HYPE: 0.2,
        }.get(state, max(0.0, min(0.3, (1.0 - opacity) * 0.2)))
        self.model.SetParameterValue(params.ParamMouthOpenY, mouth_open)
        if state == NezukoState.SLEEPING:
            self.model.SetParameterValue(params.ParamEyeLOpen, 0.05)
            self.model.SetParameterValue(params.ParamEyeROpen, 0.05)
        elif state == NezukoState.DND:
            self.model.SetParameterValue(params.ParamEyeLOpen, 0.0)
            self.model.SetParameterValue(params.ParamEyeROpen, 0.0)
        self.model.Update()

    def apply_state(self, state: NezukoState) -> None:
        if self.model is None or state == self._current_state:
            return

        self._current_state = state
        self._apply_expression_for_state(state)

        if state in {NezukoState.SLEEPING, NezukoState.DND}:
            self.model.StopAllMotions()
            self.model.SetAutoBlinkEnable(state != NezukoState.SLEEPING)
            self.model.SetAutoBreathEnable(state != NezukoState.DND)
            return

        self.model.SetAutoBlinkEnable(True)
        self.model.SetAutoBreathEnable(True)
        motion_group = self._motion_group_for_state(state)
        if motion_group is None:
            return

        priority = getattr(self.runtime.MotionPriority, "NORMAL", 2)
        if motion_group == "Idle":
            priority = getattr(self.runtime.MotionPriority, "IDLE", 1)
        if state in {NezukoState.GREETING, NezukoState.HYPE}:
            priority = getattr(self.runtime.MotionPriority, "FORCE", priority)
        try:
            self.model.StartRandomMotion(motion_group, priority)
        except Exception:
            pass

    def _motion_group_for_state(self, state: NezukoState) -> str | None:
        if not self.motion_groups:
            return None
        available = set(self.motion_groups)
        if state in {NezukoState.GREETING, NezukoState.HYPE} and "TapBody" in available:
            return "TapBody"
        if state in {NezukoState.IDLE, NezukoState.WORK, NezukoState.SLEEPING} and "Idle" in available:
            return "Idle"
        if "Idle" in available:
            return "Idle"
        return next(iter(self.motion_groups))

    def _apply_expression_for_state(self, state: NezukoState) -> None:
        if self.model is None or not self.expression_ids:
            return

        mapping = {
            NezukoState.GREETING: 0,
            NezukoState.IDLE: 1,
            NezukoState.WORK: 2,
            NezukoState.HYPE: 4,
            NezukoState.SLEEPING: 6,
            NezukoState.DND: 7,
        }
        expression_index = mapping.get(state, 0) % len(self.expression_ids)
        self.model.SetExpression(self.expression_ids[expression_index])

    def draw(self) -> None:
        if self.model is not None:
            self.runtime.clearBuffer(0.0, 0.0, 0.0, 0.0)
            self.model.Draw()

    def shutdown(self) -> None:
        if self.runtime is None or not self._initialized:
            return
        try:
            self.runtime.glRelease()
        finally:
            self.runtime.dispose()
            self.runtime = None
            self.model = None
            self.motion_groups = {}
            self.expression_ids = []
            self._current_state = None
            self._initialized = False
