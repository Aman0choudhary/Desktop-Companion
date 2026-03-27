from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class AppCommand:
    name: str
    payload: dict[str, object] = field(default_factory=dict)
