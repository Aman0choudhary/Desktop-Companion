import unittest

from core.activity_monitor import ActivityMonitor


class ActivityMonitorTests(unittest.TestCase):
    def test_keyboard_activity_counts_as_typing(self) -> None:
        monitor = ActivityMonitor(typing_grace_seconds=3.0, typing_burst_threshold=3)
        monitor.record_keyboard_activity(now=1.0)
        monitor.record_keyboard_activity(now=1.5)
        monitor.record_keyboard_activity(now=2.0)

        snapshot = monitor.snapshot(now=2.1)
        self.assertEqual(snapshot.recent_keypresses, 3)
        self.assertTrue(snapshot.is_typing)
        self.assertAlmostEqual(snapshot.idle_seconds, 0.1, places=3)

    def test_old_keypresses_age_out(self) -> None:
        monitor = ActivityMonitor(typing_grace_seconds=2.0, typing_burst_threshold=2)
        monitor.record_keyboard_activity(now=1.0)
        monitor.record_keyboard_activity(now=1.5)

        snapshot = monitor.snapshot(now=4.0)
        self.assertEqual(snapshot.recent_keypresses, 0)
        self.assertFalse(snapshot.is_typing)

    def test_status_defaults_to_not_running(self) -> None:
        monitor = ActivityMonitor(typing_grace_seconds=2.0, typing_burst_threshold=2)
        status = monitor.status()
        self.assertFalse(status.hooks_enabled)
        self.assertIn("not running", status.message.lower())

    def test_stop_is_idempotent(self) -> None:
        monitor = ActivityMonitor(typing_grace_seconds=2.0, typing_burst_threshold=2)
        monitor.stop()
        monitor.stop()
        self.assertFalse(monitor.status().hooks_enabled)


if __name__ == "__main__":
    unittest.main()
