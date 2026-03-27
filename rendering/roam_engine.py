from __future__ import annotations

from dataclasses import dataclass
from math import dist
from random import Random

from core.state_machine import NezukoState


@dataclass(slots=True)
class RoamBounds:
    width: int
    height: int
    margin: int


@dataclass(slots=True)
class CharacterPose:
    x: float
    y: float
    facing_right: bool
    opacity: float


class RoamEngine:
    def __init__(
        self,
        bounds: RoamBounds,
        sprite_width: int,
        sprite_height: int,
        speed_px_per_second: float,
        min_pause_seconds: float,
        max_pause_seconds: float,
        rng: Random | None = None,
    ) -> None:
        self.bounds = bounds
        self.sprite_width = sprite_width
        self.sprite_height = sprite_height
        self.speed_px_per_second = speed_px_per_second
        self.min_pause_seconds = min_pause_seconds
        self.max_pause_seconds = max_pause_seconds
        self.rng = rng or Random()

        self.x = float(self.bounds.margin)
        self.y = float(self.bounds.height - self.sprite_height - self.bounds.margin)
        self.target_x, self.target_y = self._random_target()
        self.wait_seconds = 0.0
        self.opacity = 1.0
        self.facing_right = True

    def update(self, dt: float, state: NezukoState) -> CharacterPose:
        if state == NezukoState.DND:
            self._move_toward(self._nearest_edge_target(), dt, speed_multiplier=1.15)
            self.opacity = max(0.1, self.opacity - (dt * 0.45))
            return self._pose()

        self.opacity = min(1.0, self.opacity + (dt * 0.8))

        if state == NezukoState.SLEEPING:
            sleep_target = (
                self.bounds.width - self.sprite_width - self.bounds.margin,
                self.bounds.height - self.sprite_height - self.bounds.margin,
            )
            self._move_toward(sleep_target, dt, speed_multiplier=0.6)
            return self._pose()

        if state == NezukoState.WORK:
            work_target = (
                self.bounds.width - self.sprite_width - self.bounds.margin,
                max(self.bounds.margin, self.bounds.height * 0.48),
            )
            self._move_toward(work_target, dt, speed_multiplier=0.9)
            return self._pose()

        if state == NezukoState.HYPE:
            hype_target = (
                max(self.bounds.margin, (self.bounds.width - self.sprite_width) / 2.0),
                max(self.bounds.margin, self.bounds.height * 0.38),
            )
            self._move_toward(hype_target, dt, speed_multiplier=1.2)
            return self._pose()

        if self.wait_seconds > 0.0:
            self.wait_seconds = max(0.0, self.wait_seconds - dt)
            return self._pose()

        if self._has_reached_target():
            self.wait_seconds = self.rng.uniform(self.min_pause_seconds, self.max_pause_seconds)
            self.target_x, self.target_y = self._random_target()
            return self._pose()

        self._move_toward((self.target_x, self.target_y), dt)
        return self._pose()

    def _pose(self) -> CharacterPose:
        return CharacterPose(
            x=self.x,
            y=self.y,
            facing_right=self.facing_right,
            opacity=self.opacity,
        )

    def _move_toward(self, target: tuple[float, float], dt: float, speed_multiplier: float = 1.0) -> None:
        target_x, target_y = target
        dx = target_x - self.x
        dy = target_y - self.y
        distance = dist((self.x, self.y), target)
        if distance <= 1e-6:
            return

        step = min(distance, self.speed_px_per_second * speed_multiplier * dt)
        self.x += dx / distance * step
        self.y += dy / distance * step
        self.facing_right = dx >= 0
        self.x = min(max(self.bounds.margin, self.x), self._max_x())
        self.y = min(max(self.bounds.margin, self.y), self._max_y())

    def _random_target(self) -> tuple[float, float]:
        return (
            float(self.rng.randint(self.bounds.margin, self._max_x())),
            float(self.rng.randint(self.bounds.margin, self._max_y())),
        )

    def _nearest_edge_target(self) -> tuple[float, float]:
        left_distance = self.x - self.bounds.margin
        right_distance = self._max_x() - self.x
        target_x = self.bounds.margin if left_distance <= right_distance else self._max_x()
        return (float(target_x), self.y)

    def _has_reached_target(self) -> bool:
        return dist((self.x, self.y), (self.target_x, self.target_y)) < 6.0

    def _max_x(self) -> int:
        return max(self.bounds.margin, self.bounds.width - self.sprite_width - self.bounds.margin)

    def _max_y(self) -> int:
        return max(self.bounds.margin, self.bounds.height - self.sprite_height - self.bounds.margin)
