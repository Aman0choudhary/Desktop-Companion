from __future__ import annotations

from dataclasses import dataclass
from time import monotonic
import tkinter as tk


@dataclass(slots=True)
class BubbleState:
    text: str = ""
    expires_at: float = 0.0


class SpeechBubble:
    def __init__(self, parent: tk.Tk, duration_seconds: float) -> None:
        self.parent = parent
        self.duration_seconds = duration_seconds
        self.state = BubbleState()

        self.window = tk.Toplevel(parent)
        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)
        self.window.withdraw()

        self.label = tk.Label(
            self.window,
            text="",
            bg="#fff8e7",
            fg="#101418",
            padx=14,
            pady=10,
            relief="solid",
            bd=2,
            font=("Segoe UI", 10, "bold"),
            wraplength=220,
            justify="center",
        )
        self.label.pack()

    def show(self, text: str, anchor_x: int, anchor_y: int) -> None:
        self.state.text = text
        self.state.expires_at = monotonic() + self.duration_seconds
        self.label.configure(text=text)
        self.update_position(anchor_x=anchor_x, anchor_y=anchor_y)
        self.window.deiconify()

    def update_position(self, anchor_x: int, anchor_y: int) -> None:
        if not self.window.winfo_viewable():
            return
        self.window.update_idletasks()
        bubble_width = self.window.winfo_width()
        bubble_height = self.window.winfo_height()
        x = anchor_x - (bubble_width // 2)
        y = anchor_y - bubble_height - 18
        self.window.geometry(f"+{x}+{y}")

    def tick(self) -> None:
        if self.window.winfo_viewable() and monotonic() >= self.state.expires_at:
            self.window.withdraw()
