from __future__ import annotations

from skills.common import SkillResponse


def handle_command(text: str) -> SkillResponse | None:
    lowered = text.lower()
    if lowered.startswith("search for "):
        query = text[11:].strip()
        if query:
            return SkillResponse(
                intent="web_search",
                message=f"Dry run: I would search the web for '{query}' once browser actions are enabled.",
            )
    if lowered.startswith("youtube ") or lowered.startswith("play "):
        topic = text.split(" ", 1)[1].strip()
        if topic:
            return SkillResponse(
                intent="web_media",
                message=f"Dry run: I would open media for '{topic}' when web actions are approved.",
            )
    return None
