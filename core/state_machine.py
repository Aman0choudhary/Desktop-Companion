from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from core.activity_monitor import ActivitySnapshot


class NezukoState(str, Enum):
    GREETING = "greeting"
    IDLE = "idle"
    WORK = "work"
    HYPE = "hype"
    SLEEPING = "sleeping"
    DND = "dnd"


@dataclass(slots=True)
class Transition:
    previous: NezukoState
    current: NezukoState
    reason: str


class StateMachine:
    def __init__(
        self,
        greeting_duration_seconds: float,
        sleep_after_seconds: float,
        hype_duration_seconds: float,
    ) -> None:
        self._greeting_duration_seconds = greeting_duration_seconds
        self._sleep_after_seconds = sleep_after_seconds
        self._hype_duration_seconds = hype_duration_seconds
        self.state = NezukoState.GREETING
        self.entered_at = 0.0

    def initialize(self, now: float) -> None:
        self.entered_at = now

    def update(self, snapshot: ActivitySnapshot) -> Transition | None:
        if self.state == NezukoState.DND:
            return None

        next_state = self._derive_state(snapshot)
        if next_state == self.state:
            return None

        previous = self.state
        self.state = next_state
        self.entered_at = snapshot.now
        return Transition(previous=previous, current=next_state, reason=self._reason_for(next_state, snapshot))

    def activate_dnd(self, now: float) -> Transition | None:
        if self.state == NezukoState.DND:
            return None
        previous = self.state
        self.state = NezukoState.DND
        self.entered_at = now
        return Transition(previous=previous, current=self.state, reason="user enabled do not disturb")

    def celebrate(self, now: float, reason: str = "celebration") -> Transition | None:
        if self.state == NezukoState.DND:
            return None
        previous = self.state
        self.state = NezukoState.HYPE
        self.entered_at = now
        return Transition(previous=previous, current=self.state, reason=reason)

    def wake(self, now: float) -> Transition:
        previous = self.state
        self.state = NezukoState.GREETING
        self.entered_at = now
        reason = "user called Nezuko back" if previous == NezukoState.DND else "manual wake"
        return Transition(previous=previous, current=self.state, reason=reason)

    def _derive_state(self, snapshot: ActivitySnapshot) -> NezukoState:
        if self.state == NezukoState.GREETING:
            if snapshot.now - self.entered_at < self._greeting_duration_seconds:
                return NezukoState.GREETING
            return NezukoState.IDLE

        if self.state == NezukoState.HYPE:
            if snapshot.now - self.entered_at < self._hype_duration_seconds:
                return NezukoState.HYPE
            return NezukoState.IDLE

        if snapshot.idle_seconds >= self._sleep_after_seconds:
            return NezukoState.SLEEPING

        if snapshot.is_typing:
            return NezukoState.WORK

        return NezukoState.IDLE

    def _reason_for(self, next_state: NezukoState, snapshot: ActivitySnapshot) -> str:
        if next_state == NezukoState.IDLE:
            return "returning to a calm roaming state"
        if next_state == NezukoState.WORK:
            return f"detected a typing burst of {snapshot.recent_keypresses} keys"
        if next_state == NezukoState.HYPE:
            return "celebrating a completed moment"
        if next_state == NezukoState.SLEEPING:
            return f"idle for {snapshot.idle_seconds:.1f} seconds"
        return ""
