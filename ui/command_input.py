from __future__ import annotations

import tkinter as tk
from typing import Callable


class CommandInput:
    def __init__(self, parent: tk.Tk, on_submit: Callable[[str], None]) -> None:
        self._parent = parent
        self._on_submit = on_submit

        self.window = tk.Toplevel(parent)
        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)
        self.window.configure(bg="#101418")
        self.window.withdraw()

        frame = tk.Frame(self.window, bg="#101418", padx=10, pady=10)
        frame.pack(fill="both", expand=True)

        self.entry = tk.Entry(
            frame,
            width=36,
            bg="#fff8e7",
            fg="#101418",
            insertbackground="#101418",
            relief="solid",
            bd=2,
            font=("Segoe UI", 10),
        )
        self.entry.pack(fill="x", expand=True)
        self.entry.bind("<Return>", self._submit)
        self.entry.bind("<Escape>", self._cancel)

    def open(self, anchor_x: int, anchor_y: int) -> None:
        self.window.deiconify()
        self.window.update_idletasks()
        x = anchor_x - (self.window.winfo_width() // 2)
        y = anchor_y - 74
        self.window.geometry(f"+{x}+{y}")
        self.entry.delete(0, tk.END)
        self.entry.focus_force()

    def is_open(self) -> bool:
        return bool(self.window.winfo_viewable())

    def _submit(self, _event: tk.Event[tk.Misc] | None = None) -> None:
        text = self.entry.get().strip()
        self.window.withdraw()
        if text:
            self._on_submit(text)

    def _cancel(self, _event: tk.Event[tk.Misc] | None = None) -> None:
        self.window.withdraw()
