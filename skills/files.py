from __future__ import annotations

from skills.common import SkillResponse


def handle_command(text: str) -> SkillResponse | None:
    lowered = text.lower()
    if lowered.startswith("find file ") or lowered.startswith("open file "):
        return SkillResponse(
            intent="files",
            message="Dry run: file commands are recognized, but I am not opening local files automatically yet.",
        )
    return None
