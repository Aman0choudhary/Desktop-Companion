import unittest

from core.brain import Brain


class BrainTests(unittest.TestCase):
    def test_focus_timer_start_and_completion(self) -> None:
        brain = Brain()
        response = brain.route_text("focus 2 seconds", now=0.0)
        self.assertEqual(response.intent, "focus_timer")
        self.assertIn("started", response.message.lower())

        pending = brain.poll(1.0)
        self.assertEqual(pending, [])

        ready = brain.poll(2.5)
        self.assertEqual(len(ready), 1)
        self.assertEqual(ready[0].requested_state, "hype")

    def test_reminder_can_be_scheduled(self) -> None:
        brain = Brain()
        response = brain.route_text("remind me to stretch in 3 seconds", now=0.0)
        self.assertEqual(response.intent, "reminders")
        self.assertIn("reminder saved", response.message.lower())

        ready = brain.poll(4.0)
        self.assertEqual(len(ready), 1)
        self.assertIn("stretch", ready[0].message.lower())

    def test_dry_run_app_command(self) -> None:
        brain = Brain()
        response = brain.route_text("open spotify", now=0.0)
        self.assertEqual(response.intent, "apps")
        self.assertIn("dry run", response.message.lower())


if __name__ == "__main__":
    unittest.main()
