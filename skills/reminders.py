from __future__ import annotations

import re
from dataclasses import dataclass

from skills.common import SkillResponse


@dataclass(slots=True)
class Reminder:
    text: str
    due_at: float
    delivered: bool = False


class ReminderSkill:
    def __init__(self) -> None:
        self._reminders: list[Reminder] = []

    def handle_command(self, text: str, now: float) -> SkillResponse | None:
        lowered = text.lower().strip()
        if lowered in {"reminder status", "reminders", "reminder list"}:
            return SkillResponse(intent="reminders", message=self.status_summary(now))

        match = re.search(
            r"remind me to (?P<task>.+?) in (?P<value>\d+)\s*(?P<unit>second|seconds|minute|minutes)\b",
            lowered,
        )
        if match is None:
            return None

        value = int(match.group("value"))
        unit = match.group("unit")
        task = match.group("task").strip()
        multiplier = 60 if unit.startswith("minute") else 1
        due_at = now + (value * multiplier)
        self._reminders.append(Reminder(text=task, due_at=due_at))
        return SkillResponse(
            intent="reminders",
            message=f"Reminder saved. I will remind you to {task} in {value} {unit}.",
        )

    def poll(self, now: float) -> list[SkillResponse]:
        ready: list[SkillResponse] = []
        for reminder in self._reminders:
            if reminder.delivered or reminder.due_at > now:
                continue
            reminder.delivered = True
            ready.append(
                SkillResponse(
                    intent="reminder_due",
                    message=f"Reminder: {reminder.text}.",
                    requested_state="hype",
                )
            )
        return ready

    def status_summary(self, now: float) -> str:
        pending = [reminder for reminder in self._reminders if not reminder.delivered and reminder.due_at > now]
        if not pending:
            return "No active reminders right now."
        return f"{len(pending)} reminder(s) are waiting."
