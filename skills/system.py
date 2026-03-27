from __future__ import annotations

from skills.common import SkillResponse


def handle_command(text: str) -> SkillResponse | None:
    lowered = text.lower()
    keywords = ("volume", "brightness", "shutdown", "restart", "sleep", "mute")
    if any(word in lowered for word in keywords):
        return SkillResponse(
            intent="system",
            message="Dry run: system controls are recognized, but I will not change your machine without approval.",
        )
    return None
