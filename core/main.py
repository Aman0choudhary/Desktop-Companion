from __future__ import annotations

from time import monotonic

from core.activity_monitor import ActivityMonitor
from core.config import DEFAULT_CONFIG, AppConfig
from core.state_machine import NezukoState, StateMachine, Transition
from live2d.animations import AnimationController
from live2d.renderer import DesktopRenderer
from live2d.roam_engine import RoamBounds, RoamEngine


class NezukoApp:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.activity_monitor = ActivityMonitor(
            typing_grace_seconds=config.typing_grace_seconds,
            typing_burst_threshold=config.typing_burst_threshold,
        )
        self.state_machine = StateMachine(
            greeting_duration_seconds=config.greeting_duration_seconds,
            sleep_after_seconds=config.sleep_after_seconds,
        )
        self.animations = AnimationController()
        self.renderer = DesktopRenderer(
            width=config.window_width,
            height=config.window_height,
            bubble_duration_seconds=config.bubble_duration_seconds,
            on_key=self.handle_key,
        )

        screen_width, screen_height = self.renderer.get_screen_size()
        self.roam_engine = RoamEngine(
            bounds=RoamBounds(
                width=max(config.window_width, screen_width),
                height=max(config.window_height, screen_height),
                margin=config.screen_margin,
            ),
            sprite_width=config.window_width,
            sprite_height=config.window_height,
            speed_px_per_second=config.roam_speed_px_per_second,
            min_pause_seconds=config.min_pause_seconds,
            max_pause_seconds=config.max_pause_seconds,
        )
        now = monotonic()
        self.state_machine.initialize(now)
        self._last_tick = now
        self.renderer.show_bubble("Prototype online. Press T to simulate typing.")

    def handle_key(self, key: str) -> None:
        now = monotonic()
        if key == "Escape":
            self.renderer.request_close()
            return

        if key.lower() == "t":
            for _ in range(self.config.typing_burst_threshold):
                self.activity_monitor.record_keyboard_activity(now)
            self.renderer.show_bubble("Work mode incoming.")
            return

        if key.lower() == "h":
            transition = self.state_machine.wake(now)
            self.activity_monitor.record_presence(now)
            self._announce_transition(transition)
            return

        if key.lower() == "d":
            if self.state_machine.state == NezukoState.DND:
                transition = self.state_machine.wake(now)
            else:
                transition = self.state_machine.activate_dnd(now)
            self._announce_transition(transition)
            return

        if key == "space":
            self.activity_monitor.record_presence(now)
            self.renderer.show_bubble("Mmmph! I am still here.")
            return

        self.activity_monitor.record_keyboard_activity(now)

    def tick(self) -> None:
        now = monotonic()
        dt = max(0.0, now - self._last_tick)
        self._last_tick = now

        snapshot = self.activity_monitor.snapshot(now)
        transition = self.state_machine.update(snapshot)
        self._announce_transition(transition)

        pose = self.roam_engine.update(dt=dt, state=self.state_machine.state)
        frame = self.animations.frame_for(self.state_machine.state, now)
        self.renderer.render(
            pose=pose,
            frame=frame,
            state_label=self.state_machine.state.value,
        )

    def _announce_transition(self, transition: Transition | None) -> None:
        if transition is None or transition.previous == transition.current:
            return

        bubble_text = {
            NezukoState.GREETING: "Hello! I am ready to roam.",
            NezukoState.IDLE: "Quiet mode. I will stay nearby.",
            NezukoState.WORK: "You are working hard. Keep going.",
            NezukoState.SLEEPING: "It is calm now. Nap time.",
            NezukoState.DND: "Do Not Disturb enabled. I will fade out.",
        }[transition.current]
        self.renderer.show_bubble(bubble_text)

    def run(self) -> int:
        self.renderer.run(self.tick, self.config.update_interval_ms)
        return 0


def main() -> int:
    app = NezukoApp(DEFAULT_CONFIG)
    return app.run()


if __name__ == "__main__":
    raise SystemExit(main())
