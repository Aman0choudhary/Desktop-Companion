from __future__ import annotations

from dataclasses import dataclass
from math import sin

from core.state_machine import NezukoState


@dataclass(slots=True)
class AnimationFrame:
    bob_offset: float
    eye_open: bool
    mood_label: str
    accent_color: str


class AnimationController:
    def frame_for(self, state: NezukoState, now: float) -> AnimationFrame:
        bob = sin(now * 2.6) * 6.0
        blink = int(now * 3.2) % 11 != 0

        if state == NezukoState.GREETING:
            return AnimationFrame(bob_offset=bob, eye_open=True, mood_label="greeting", accent_color="#ff8fb1")
        if state == NezukoState.WORK:
            return AnimationFrame(bob_offset=bob / 2.0, eye_open=True, mood_label="work", accent_color="#ffd166")
        if state == NezukoState.SLEEPING:
            return AnimationFrame(bob_offset=1.0, eye_open=False, mood_label="sleep", accent_color="#9bb1ff")
        if state == NezukoState.DND:
            return AnimationFrame(bob_offset=0.0, eye_open=False, mood_label="dnd", accent_color="#8d99ae")
        return AnimationFrame(bob_offset=bob, eye_open=blink, mood_label="idle", accent_color="#7bd389")
