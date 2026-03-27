import unittest
from random import Random

from core.state_machine import NezukoState
from rendering.roam_engine import RoamBounds, RoamEngine


class RoamEngineTests(unittest.TestCase):
    def test_idle_motion_stays_inside_bounds(self) -> None:
        engine = RoamEngine(
            bounds=RoamBounds(width=800, height=600, margin=20),
            sprite_width=200,
            sprite_height=200,
            speed_px_per_second=160.0,
            min_pause_seconds=0.5,
            max_pause_seconds=1.0,
            rng=Random(7),
        )
        for _ in range(200):
            pose = engine.update(dt=0.05, state=NezukoState.IDLE)
            self.assertGreaterEqual(pose.x, 20)
            self.assertLessEqual(pose.x, 580)
            self.assertGreaterEqual(pose.y, 20)
            self.assertLessEqual(pose.y, 380)

    def test_dnd_reduces_opacity(self) -> None:
        engine = RoamEngine(
            bounds=RoamBounds(width=800, height=600, margin=20),
            sprite_width=200,
            sprite_height=200,
            speed_px_per_second=160.0,
            min_pause_seconds=0.5,
            max_pause_seconds=1.0,
            rng=Random(7),
        )
        starting_opacity = engine.update(dt=0.05, state=NezukoState.IDLE).opacity
        dnd_opacity = engine.update(dt=0.5, state=NezukoState.DND).opacity
        self.assertLess(dnd_opacity, starting_opacity)


if __name__ == "__main__":
    unittest.main()
