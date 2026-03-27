import unittest

from core.activity_monitor import ActivitySnapshot
from core.state_machine import NezukoState, StateMachine


def make_snapshot(now: float, idle_seconds: float, recent_keypresses: int, is_typing: bool) -> ActivitySnapshot:
    return ActivitySnapshot(
        now=now,
        idle_seconds=idle_seconds,
        recent_keypresses=recent_keypresses,
        is_typing=is_typing,
    )


class StateMachineTests(unittest.TestCase):
    def test_greeting_flows_into_idle(self) -> None:
        machine = StateMachine(greeting_duration_seconds=2.0, sleep_after_seconds=10.0)
        machine.initialize(0.0)
        transition = machine.update(make_snapshot(now=2.5, idle_seconds=0.2, recent_keypresses=0, is_typing=False))
        self.assertIsNotNone(transition)
        self.assertEqual(transition.current, NezukoState.IDLE)

    def test_typing_switches_to_work(self) -> None:
        machine = StateMachine(greeting_duration_seconds=1.0, sleep_after_seconds=10.0)
        machine.initialize(0.0)
        machine.update(make_snapshot(now=1.2, idle_seconds=0.2, recent_keypresses=0, is_typing=False))
        transition = machine.update(make_snapshot(now=1.5, idle_seconds=0.1, recent_keypresses=4, is_typing=True))
        self.assertIsNotNone(transition)
        self.assertEqual(transition.current, NezukoState.WORK)

    def test_long_idle_switches_to_sleep(self) -> None:
        machine = StateMachine(greeting_duration_seconds=1.0, sleep_after_seconds=5.0)
        machine.initialize(0.0)
        machine.update(make_snapshot(now=1.2, idle_seconds=0.2, recent_keypresses=0, is_typing=False))
        transition = machine.update(make_snapshot(now=6.5, idle_seconds=5.2, recent_keypresses=0, is_typing=False))
        self.assertIsNotNone(transition)
        self.assertEqual(transition.current, NezukoState.SLEEPING)

    def test_dnd_persists_until_wake(self) -> None:
        machine = StateMachine(greeting_duration_seconds=1.0, sleep_after_seconds=5.0)
        machine.initialize(0.0)
        machine.activate_dnd(2.0)
        transition = machine.update(make_snapshot(now=20.0, idle_seconds=18.0, recent_keypresses=0, is_typing=False))
        self.assertIsNone(transition)
        wake = machine.wake(21.0)
        self.assertEqual(wake.current, NezukoState.GREETING)


if __name__ == "__main__":
    unittest.main()
