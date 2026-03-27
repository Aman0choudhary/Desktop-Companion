from __future__ import annotations

from skills.common import SkillResponse


def handle_command(text: str) -> SkillResponse:
    lowered = text.lower().strip()
    if "thank" in lowered:
        return SkillResponse(intent="chat", message="Mmmph! You are welcome.")
    if "hello" in lowered or "hi" == lowered:
        return SkillResponse(intent="chat", message="Hello. I am staying close by.")
    if "how are you" in lowered:
        return SkillResponse(intent="chat", message="I am doing well. Quiet, alert, and ready to help.")
    return SkillResponse(
        intent="chat",
        message="I heard you. Voice, app control, and real chat are the next layers to build.",
    )
