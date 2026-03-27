from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass
from typing import Callable

from live2d.animations import AnimationFrame
from live2d.roam_engine import CharacterPose
from ui.speech_bubble import SpeechBubble


@dataclass(slots=True)
class DrawPalette:
    body: str = "#161a1d"
    outline: str = "#000000"
    scarf: str = "#f94144"
    eyes: str = "#ffffff"
    text: str = "#f8f9fa"


class DesktopRenderer:
    def __init__(
        self,
        width: int,
        height: int,
        bubble_duration_seconds: float,
        on_key: Callable[[str], None] | None = None,
    ) -> None:
        self.width = width
        self.height = height
        self._on_key = on_key
        self._close_requested = False
        self.palette = DrawPalette()

        self.root = tk.Tk()
        self.root.title("Nezuko Prototype")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.configure(bg="#101418")
        self.root.geometry(f"{width}x{height}+40+40")
        self.root.bind("<Escape>", self._forward_key)
        self.root.bind("<Key>", self._forward_key)
        self.root.bind("<Button-1>", self._focus)

        self.canvas = tk.Canvas(
            self.root,
            width=width,
            height=height,
            bg="#101418",
            highlightthickness=0,
        )
        self.canvas.pack(fill="both", expand=True)

        self.state_text = self.canvas.create_text(
            width // 2,
            height - 18,
            text="idle",
            fill=self.palette.text,
            font=("Segoe UI", 10, "bold"),
        )
        self.speech_bubble = SpeechBubble(self.root, duration_seconds=bubble_duration_seconds)

    def get_screen_size(self) -> tuple[int, int]:
        return self.root.winfo_screenwidth(), self.root.winfo_screenheight()

    def show_bubble(self, text: str) -> None:
        x = self.root.winfo_x() + (self.width // 2)
        y = self.root.winfo_y()
        self.speech_bubble.show(text=text, anchor_x=x, anchor_y=y)

    def render(self, pose: CharacterPose, frame: AnimationFrame, state_label: str) -> None:
        alpha = max(0.2, pose.opacity)
        self.root.attributes("-alpha", alpha)
        self.root.geometry(f"{self.width}x{self.height}+{int(pose.x)}+{int(pose.y + frame.bob_offset)}")
        self.canvas.delete("character")

        center_x = self.width // 2
        head_top = 28
        head_bottom = 148
        body_top = 116
        body_bottom = self.height - 26

        self.canvas.create_oval(
            center_x - 60,
            head_top,
            center_x + 60,
            head_bottom,
            fill=frame.accent_color,
            outline=self.palette.outline,
            width=3,
            tags="character",
        )
        self.canvas.create_rectangle(
            center_x - 72,
            body_top,
            center_x + 72,
            body_bottom,
            fill=self.palette.body,
            outline=self.palette.outline,
            width=3,
            tags="character",
        )
        self.canvas.create_polygon(
            center_x - 72,
            body_top + 10,
            center_x,
            body_bottom,
            center_x + 72,
            body_top + 10,
            fill=self.palette.body,
            outline=self.palette.outline,
            width=3,
            tags="character",
        )
        self.canvas.create_rectangle(
            center_x - 75,
            body_top + 18,
            center_x + 75,
            body_top + 42,
            fill=self.palette.scarf,
            outline=self.palette.outline,
            width=2,
            tags="character",
        )

        eye_y = 90
        eye_width = 18
        eye_height = 10 if frame.eye_open else 2
        left_eye_x = center_x - 24
        right_eye_x = center_x + 24
        for eye_x in (left_eye_x, right_eye_x):
            self.canvas.create_oval(
                eye_x - eye_width // 2,
                eye_y - eye_height // 2,
                eye_x + eye_width // 2,
                eye_y + eye_height // 2,
                fill=self.palette.eyes,
                outline=self.palette.outline,
                width=2,
                tags="character",
            )

        mouth_y = 120 if frame.eye_open else 116
        mouth_span = 18 if frame.mood_label != "sleep" else 10
        self.canvas.create_line(
            center_x - mouth_span,
            mouth_y,
            center_x + mouth_span,
            mouth_y,
            fill=self.palette.outline,
            width=3,
            smooth=True,
            tags="character",
        )
        direction = "right" if pose.facing_right else "left"
        self.canvas.itemconfigure(self.state_text, text=f"{state_label} | facing {direction}")
        self.speech_bubble.update_position(
            anchor_x=self.root.winfo_x() + (self.width // 2),
            anchor_y=self.root.winfo_y(),
        )
        self.speech_bubble.tick()

    def request_close(self) -> None:
        self._close_requested = True
        self.root.destroy()

    def run(self, tick: Callable[[], None], interval_ms: int) -> None:
        self.root.after(interval_ms, lambda: self._tick_loop(tick, interval_ms))
        self.root.mainloop()

    def _tick_loop(self, tick: Callable[[], None], interval_ms: int) -> None:
        if self._close_requested:
            return
        tick()
        self.root.after(interval_ms, lambda: self._tick_loop(tick, interval_ms))

    def _forward_key(self, event: tk.Event[tk.Misc]) -> None:
        if self._on_key is not None:
            self._on_key(event.keysym)

    def _focus(self, _event: tk.Event[tk.Misc]) -> None:
        self.root.focus_force()
