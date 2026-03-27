from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class SkillResponse:
    intent: str
    message: str
    requested_state: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)
