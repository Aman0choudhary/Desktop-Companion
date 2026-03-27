from __future__ import annotations

from skills import ai_chat, apps, files, system, web
from skills.common import SkillResponse
from skills.focus_timer import FocusTimerSkill
from skills.reminders import ReminderSkill


class Brain:
    """Routes safe typed commands to dry-run skills and in-memory timers."""

    def __init__(self) -> None:
        self.focus_timer = FocusTimerSkill()
        self.reminders = ReminderSkill()

    def route_text(self, text: str, now: float) -> SkillResponse:
        normalized = text.strip()
        lowered = normalized.lower()
        if not lowered:
            return SkillResponse(intent="empty", message="I did not catch a command.")

        if lowered in {"help", "commands"}:
            return SkillResponse(
                intent="help",
                message=(
                    "Try: focus 10 seconds, timer status, remind me to stretch in 20 seconds, "
                    "open spotify, search for lo-fi beats, do not disturb, wake, or status."
                ),
            )

        if lowered in {"dnd", "do not disturb"}:
            return SkillResponse(intent="dnd", message="Okay. I will keep quiet.", requested_state="dnd")

        if lowered in {"wake", "hey nezuko", "come back"}:
            return SkillResponse(intent="wake", message="I am back.", requested_state="greeting")

        if lowered in {"status", "how are you"}:
            timer_summary = self.focus_timer.status_summary(now)
            reminder_summary = self.reminders.status_summary(now)
            return SkillResponse(
                intent="status",
                message=f"I am roaming. {timer_summary} {reminder_summary}",
            )

        focus_response = self.focus_timer.handle_command(lowered, now)
        if focus_response is not None:
            return focus_response

        reminder_response = self.reminders.handle_command(lowered, now)
        if reminder_response is not None:
            return reminder_response

        for handler in (apps.handle_command, web.handle_command, files.handle_command, system.handle_command):
            response = handler(normalized)
            if response is not None:
                return response

        return ai_chat.handle_command(normalized)

    def poll(self, now: float) -> list[SkillResponse]:
        responses: list[SkillResponse] = []
        responses.extend(self.focus_timer.poll(now))
        responses.extend(self.reminders.poll(now))
        return responses
