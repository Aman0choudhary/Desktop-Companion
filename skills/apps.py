from __future__ import annotations

from skills.common import SkillResponse


def handle_command(text: str) -> SkillResponse | None:
    lowered = text.lower()
    for verb in ("open ", "launch ", "start "):
        if lowered.startswith(verb):
            app_name = text[len(verb) :].strip()
            if app_name:
                return SkillResponse(
                    intent="apps",
                    message=f"Dry run: I would open {app_name} after you approve real app launching.",
                )
    return None
