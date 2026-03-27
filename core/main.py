from __future__ import annotations

from pathlib import Path
from queue import Empty, Queue
from time import monotonic

from core.activity_monitor import ActivityMonitor
from core.brain import Brain
from core.commands import AppCommand
from core.config import AppConfig, load_app_config, save_app_config
from core.state_machine import NezukoState, StateMachine, Transition
from core.status import AppStatusStore
from core.voice_pipeline import VoicePipeline, VoicePipelineConfig
from rendering.animations import AnimationController
from rendering.renderer import DesktopRenderer
from rendering.roam_engine import RoamBounds, RoamEngine
from startup import autostart
from ui.settings_window import SettingsWindowController
from ui.tray_icon import TrayIconController


class NezukoApp:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.command_queue: Queue[AppCommand] = Queue()
        self.status_store = AppStatusStore()
        self.settings_window = SettingsWindowController(self.enqueue_command)
        self.tray_icon = TrayIconController(self.status_store, self.enqueue_command)
        self._autostart_enabled = autostart.is_enabled()
        self.activity_monitor = ActivityMonitor(
            typing_grace_seconds=config.typing_grace_seconds,
            typing_burst_threshold=config.typing_burst_threshold,
        )
        if config.use_global_activity_hooks:
            self.activity_monitor.start_global_hooks()
        self.brain = Brain()
        self.voice_pipeline: VoicePipeline | None = None
        self.state_machine = StateMachine(
            greeting_duration_seconds=config.greeting_duration_seconds,
            sleep_after_seconds=config.sleep_after_seconds,
            hype_duration_seconds=config.hype_duration_seconds,
        )
        self.animations = AnimationController()
        self.renderer = DesktopRenderer(
            width=config.window_width,
            height=config.window_height,
            bubble_duration_seconds=config.bubble_duration_seconds,
            on_key=self.handle_key,
            on_command=self.handle_command,
            click_through=config.click_through_window,
            model_path=config.live2d_model_path or None,
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
        if config.enable_voice_pipeline:
            self._start_voice_pipeline()
        self._refresh_status()
        self.tray_icon.start()
        self.renderer.show_bubble("Prototype online. Press Enter for commands.")

    def enqueue_command(self, command: AppCommand) -> None:
        self.command_queue.put(command)

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

        if key.lower() == "v":
            if self.voice_pipeline is None:
                self.renderer.show_bubble("Voice pipeline is disabled in settings.")
            else:
                self.renderer.show_bubble(self.voice_pipeline.wake_word.status().message)
            return

        if key == "space":
            self.activity_monitor.record_presence(now)
            self.renderer.show_bubble("Mmmph! I am still here.")
            return

        self.activity_monitor.record_keyboard_activity(now)

    def handle_command(self, text: str) -> None:
        now = monotonic()
        self.activity_monitor.record_presence(now)
        self._apply_skill_response(self.brain.route_text(text, now), now)

    def tick(self) -> None:
        now = monotonic()
        dt = max(0.0, now - self._last_tick)
        self._last_tick = now

        self._process_pending_commands()
        if self.voice_pipeline is not None:
            for event in self.voice_pipeline.poll_events():
                self._handle_voice_event(event, now)

        if self.state_machine.state != NezukoState.DND:
            for response in self.brain.poll(now):
                self._apply_skill_response(response, now)

        snapshot = self.activity_monitor.snapshot(now)
        transition = self.state_machine.update(snapshot)
        self._announce_transition(transition)

        pose = self.roam_engine.update(dt=dt, state=self.state_machine.state)
        frame = self.animations.frame_for(self.state_machine.state, now)
        self.renderer.render(
            pose=pose,
            frame=frame,
            state=self.state_machine.state,
        )
        self._refresh_status()

    def _apply_skill_response(self, response, now: float) -> None:
        if response.requested_state == "dnd":
            self._announce_transition(self.state_machine.activate_dnd(now))
        elif response.requested_state == "greeting":
            self._announce_transition(self.state_machine.wake(now))
        elif response.requested_state == "hype":
            self._announce_transition(self.state_machine.celebrate(now, reason=response.intent))

        self.renderer.show_bubble(response.message)
        if self.voice_pipeline is not None and self.state_machine.state != NezukoState.DND:
            self.voice_pipeline.speak(response.message)

    def _announce_transition(self, transition: Transition | None) -> None:
        if transition is None or transition.previous == transition.current:
            return

        bubble_text = {
            NezukoState.GREETING: "Hello! I am ready to roam.",
            NezukoState.IDLE: "Quiet mode. I will stay nearby.",
            NezukoState.WORK: "You are working hard. Keep going.",
            NezukoState.HYPE: "Yay. That deserves a celebration.",
            NezukoState.SLEEPING: "It is calm now. Nap time.",
            NezukoState.DND: "Do Not Disturb enabled. I will fade out.",
        }[transition.current]
        self.renderer.show_bubble(bubble_text)

    def _handle_voice_event(self, event, now: float) -> None:
        if event.kind == "voice_error":
            self.renderer.show_bubble(event.text)
            return
        if event.kind == "voice_status":
            self.renderer.show_bubble(event.text)
            return
        if event.kind == "wake_detected":
            self.activity_monitor.record_presence(now)
            self.renderer.show_bubble(f"{event.text} detected. Listening...")
            return
        if event.kind == "transcript":
            transcript = event.text.strip()
            if not transcript:
                self.renderer.show_bubble("I did not catch that clearly.")
                return
            self.renderer.show_bubble(f"You said: {transcript}")
            self.activity_monitor.record_presence(now)
            self._apply_skill_response(self.brain.route_text(transcript, now), now)

    def _start_voice_pipeline(self) -> None:
        if self.voice_pipeline is not None:
            return

        wake_model_path = self.config.wake_word_model_path.strip()
        self.voice_pipeline = VoicePipeline(
            VoicePipelineConfig(
                wake_word_phrase=self.config.wake_word_phrase,
                wake_word_model_name=self.config.wake_word_model_name,
                wake_word_model_path=Path(wake_model_path) if wake_model_path else None,
                wake_word_threshold=self.config.wake_word_threshold,
                sample_rate_hz=self.config.voice_sample_rate_hz,
                chunk_size=self.config.voice_chunk_size,
                capture_max_seconds=self.config.voice_capture_max_seconds,
                end_silence_seconds=self.config.voice_end_silence_seconds,
                silence_rms_threshold=self.config.voice_rms_silence_threshold,
                whisper_model_size=self.config.whisper_model_size,
                whisper_compute_type=self.config.whisper_compute_type,
                edge_tts_voice=self.config.edge_tts_voice,
                wake_models_dir=config_root() / "assets" / "voice" / "openwakeword_models",
                whisper_download_dir=config_root() / "assets" / "voice" / "whisper_models",
            )
        )
        self.voice_pipeline.start()

    def _stop_voice_pipeline(self) -> None:
        if self.voice_pipeline is None:
            return
        self.voice_pipeline.stop()
        self.voice_pipeline = None

    def _restart_voice_pipeline(self) -> None:
        self._stop_voice_pipeline()
        if self.config.enable_voice_pipeline:
            self._start_voice_pipeline()

    def _process_pending_commands(self) -> None:
        while True:
            try:
                command = self.command_queue.get_nowait()
            except Empty:
                return
            self._apply_app_command(command)

    def _apply_app_command(self, command: AppCommand) -> None:
        if command.name == "quit":
            self.renderer.request_close()
            return

        if command.name == "toggle_dnd":
            now = monotonic()
            if self.state_machine.state == NezukoState.DND:
                self._announce_transition(self.state_machine.wake(now))
            else:
                self._announce_transition(self.state_machine.activate_dnd(now))
            return

        if command.name == "toggle_voice":
            self.config.enable_voice_pipeline = not self.config.enable_voice_pipeline
            save_app_config(self.config)
            self._restart_voice_pipeline()
            message = "Voice pipeline enabled." if self.config.enable_voice_pipeline else "Voice pipeline disabled."
            self.renderer.show_bubble(message)
            return

        if command.name == "toggle_click_through":
            self.config.click_through_window = not self.config.click_through_window
            self.renderer.set_click_through(self.config.click_through_window)
            save_app_config(self.config)
            message = "Click-through enabled." if self.config.click_through_window else "Click-through disabled."
            self.renderer.show_bubble(message)
            return

        if command.name == "toggle_autostart":
            if self._autostart_enabled:
                autostart.disable()
                self._autostart_enabled = False
                self.renderer.show_bubble("Autostart disabled.")
            else:
                autostart.enable()
                self._autostart_enabled = True
                self.renderer.show_bubble("Autostart enabled.")
            return

        if command.name == "show_settings":
            shown = self.settings_window.show(self.config, self._autostart_enabled)
            if not shown:
                self.renderer.show_bubble("Settings window is already open.")
            return

        if command.name == "save_settings":
            config = command.payload.get("config")
            if isinstance(config, AppConfig):
                autostart_enabled = bool(command.payload.get("autostart_enabled", self._autostart_enabled))
                self._save_settings(config, autostart_enabled)
            return

        if command.name == "bubble":
            text = str(command.payload.get("text", "")).strip()
            if text:
                self.renderer.show_bubble(text)

    def _save_settings(self, new_config: AppConfig, autostart_enabled: bool) -> None:
        previous_config = self.config
        voice_fields = (
            "enable_voice_pipeline",
            "wake_word_phrase",
            "wake_word_model_name",
            "wake_word_model_path",
            "wake_word_threshold",
            "voice_sample_rate_hz",
            "voice_chunk_size",
            "voice_capture_max_seconds",
            "voice_end_silence_seconds",
            "voice_rms_silence_threshold",
            "whisper_model_size",
            "whisper_compute_type",
            "edge_tts_voice",
        )
        voice_changed = any(getattr(previous_config, field) != getattr(new_config, field) for field in voice_fields)
        model_changed = previous_config.live2d_model_path != new_config.live2d_model_path
        hooks_changed = previous_config.use_global_activity_hooks != new_config.use_global_activity_hooks
        click_changed = previous_config.click_through_window != new_config.click_through_window

        self.config = new_config
        save_app_config(self.config)

        if hooks_changed:
            if self.config.use_global_activity_hooks:
                self.activity_monitor.start_global_hooks()
            else:
                self.activity_monitor.stop()
        if click_changed:
            self.renderer.set_click_through(self.config.click_through_window)
        if voice_changed:
            self._restart_voice_pipeline()

        if autostart_enabled != self._autostart_enabled:
            if autostart_enabled:
                autostart.enable()
                self._autostart_enabled = True
            else:
                autostart.disable()
                self._autostart_enabled = False

        message = "Settings saved."
        if model_changed:
            message = "Settings saved. Restart to load the new Live2D model."
        self.renderer.show_bubble(message)

    def _refresh_status(self) -> None:
        previous = self.status_store.snapshot()
        next_values = dict(
            dnd_enabled=self.state_machine.state == NezukoState.DND,
            voice_enabled=self.config.enable_voice_pipeline and self.voice_pipeline is not None,
            click_through_enabled=self.config.click_through_window,
            autostart_enabled=self._autostart_enabled,
            active_model_name=self.renderer.active_model_name(),
        )
        if (
            previous.dnd_enabled == next_values["dnd_enabled"]
            and previous.voice_enabled == next_values["voice_enabled"]
            and previous.click_through_enabled == next_values["click_through_enabled"]
            and previous.autostart_enabled == next_values["autostart_enabled"]
            and previous.active_model_name == next_values["active_model_name"]
        ):
            return
        self.status_store.update(**next_values)
        self.tray_icon.refresh()

    def run(self) -> int:
        try:
            self.renderer.run(self.tick, self.config.update_interval_ms)
            return 0
        finally:
            self._stop_voice_pipeline()
            self.tray_icon.stop()
            self.activity_monitor.stop()


def config_root() -> Path:
    return Path(__file__).resolve().parent.parent


def main() -> int:
    app = NezukoApp(load_app_config())
    return app.run()


if __name__ == "__main__":
    raise SystemExit(main())
