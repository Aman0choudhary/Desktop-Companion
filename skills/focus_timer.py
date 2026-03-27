from __future__ import annotations

import re
from dataclasses import dataclass

from skills.common import SkillResponse


@dataclass(slots=True)
class FocusTimerSession:
    duration_seconds: int
    started_at: float
    label: str
    completion_announced: bool = False

    def remaining_seconds(self, now: float) -> int:
        return max(0, int(self.duration_seconds - (now - self.started_at)))

    def is_complete(self, now: float) -> bool:
        return now - self.started_at >= self.duration_seconds


class FocusTimerSkill:
    def __init__(self) -> None:
        self.active_session: FocusTimerSession | None = None

    def handle_command(self, text: str, now: float) -> SkillResponse | None:
        lowered = text.lower().strip()
        if lowered in {"timer status", "focus status", "status timer"}:
            return SkillResponse(intent="focus_timer", message=self.status_summary(now))

        if lowered in {"cancel timer", "stop timer", "cancel focus", "stop focus"}:
            if self.active_session is None:
                return SkillResponse(intent="focus_timer", message="There is no active focus timer right now.")
            self.active_session = None
            return SkillResponse(intent="focus_timer", message="Focus timer cancelled.")

        match = re.search(
            r"(?:focus|timer)(?: for)? (?P<value>\d+)\s*(?P<unit>second|seconds|minute|minutes)\b",
            lowered,
        )
        if match is None:
            return None

        value = int(match.group("value"))
        unit = match.group("unit")
        multiplier = 60 if unit.startswith("minute") else 1
        duration_seconds = value * multiplier
        label = "focus timer"
        self.active_session = FocusTimerSession(
            duration_seconds=duration_seconds,
            started_at=now,
            label=label,
        )
        return SkillResponse(
            intent="focus_timer",
            message=f"Focus timer started for {value} {unit}. I will cheer when it finishes.",
        )

    def poll(self, now: float) -> list[SkillResponse]:
        if self.active_session is None or not self.active_session.is_complete(now):
            return []
        if self.active_session.completion_announced:
            return []
        self.active_session.completion_announced = True
        finished_label = self.active_session.label
        self.active_session = None
        return [
            SkillResponse(
                intent="focus_timer_complete",
                message=f"{finished_label.title()} complete. You did it.",
                requested_state="hype",
            )
        ]

    def status_summary(self, now: float) -> str:
        if self.active_session is None:
            return "No focus timer is running."
        remaining = self.active_session.remaining_seconds(now)
        return f"Focus timer running. {remaining} seconds left."
