from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class BrainDecision:
    intent: str
    response: str


class Brain:
    """A tiny command router placeholder for later voice integration."""

    def route_text(self, text: str) -> BrainDecision:
        normalized = text.strip().lower()
        if normalized in {"dnd", "do not disturb"}:
            return BrainDecision(intent="dnd", response="Okay, I will keep quiet.")
        if normalized in {"wake", "hey nezuko", "hello"}:
            return BrainDecision(intent="wake", response="I am here.")
        if normalized in {"status", "how are you"}:
            return BrainDecision(intent="status", response="I am roaming and keeping watch.")
        return BrainDecision(intent="chat", response="I heard you. Voice and chat are next on the roadmap.")
