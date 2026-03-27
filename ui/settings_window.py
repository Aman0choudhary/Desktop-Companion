from __future__ import annotations

from dataclasses import asdict
from threading import Lock, Thread
import tkinter as tk
from tkinter import filedialog

from core.commands import AppCommand
from core.config import AppConfig


class SettingsWindowController:
    def __init__(self, on_command) -> None:
        self._on_command = on_command
        self._lock = Lock()
        self._is_open = False

    def show(self, config: AppConfig, autostart_enabled: bool) -> bool:
        with self._lock:
            if self._is_open:
                return False
            self._is_open = True

        Thread(
            target=self._run_window,
            args=(config, autostart_enabled),
            name="nezuko-settings-window",
            daemon=True,
        ).start()
        return True

    def _run_window(self, config: AppConfig, autostart_enabled: bool) -> None:
        root = tk.Tk()
        root.title("Nezuko Settings")
        root.geometry("540x420")
        root.resizable(False, False)
        root.configure(bg="#f7efe7")

        container = tk.Frame(root, bg="#f7efe7", padx=18, pady=18)
        container.pack(fill="both", expand=True)

        tk.Label(
            container,
            text="Nezuko Companion Settings",
            font=("Segoe UI", 14, "bold"),
            bg="#f7efe7",
            fg="#231f20",
        ).pack(anchor="w")
        tk.Label(
            container,
            text="Voice changes reload immediately. Live2D model changes apply after restart.",
            font=("Segoe UI", 9),
            bg="#f7efe7",
            fg="#5f4b4b",
        ).pack(anchor="w", pady=(4, 16))

        voice_enabled = tk.BooleanVar(value=config.enable_voice_pipeline)
        hooks_enabled = tk.BooleanVar(value=config.use_global_activity_hooks)
        click_through_enabled = tk.BooleanVar(value=config.click_through_window)
        autostart_var = tk.BooleanVar(value=autostart_enabled)
        wake_phrase_var = tk.StringVar(value=config.wake_word_phrase)
        wake_model_name_var = tk.StringVar(value=config.wake_word_model_name)
        wake_model_path_var = tk.StringVar(value=config.wake_word_model_path)
        live2d_model_path_var = tk.StringVar(value=config.live2d_model_path)
        tts_voice_var = tk.StringVar(value=config.edge_tts_voice)

        for label, variable in (
            ("Enable Voice Pipeline", voice_enabled),
            ("Use Global Activity Hooks", hooks_enabled),
            ("Enable Click Through", click_through_enabled),
            ("Start With Windows", autostart_var),
        ):
            tk.Checkbutton(
                container,
                text=label,
                variable=variable,
                bg="#f7efe7",
                activebackground="#f7efe7",
                anchor="w",
                font=("Segoe UI", 10),
            ).pack(fill="x", pady=2)

        def add_labeled_entry(label_text: str, variable: tk.StringVar, browse_kind: str | None = None) -> None:
            row = tk.Frame(container, bg="#f7efe7")
            row.pack(fill="x", pady=6)
            tk.Label(row, text=label_text, width=18, anchor="w", bg="#f7efe7", font=("Segoe UI", 10, "bold")).pack(side="left")
            tk.Entry(row, textvariable=variable, font=("Segoe UI", 10)).pack(side="left", fill="x", expand=True)
            if browse_kind is None:
                return

            def browse() -> None:
                filetypes = [("All files", "*.*")]
                if browse_kind == "live2d":
                    filetypes.insert(0, ("Live2D model", "*.model3.json"))
                elif browse_kind == "onnx":
                    filetypes.insert(0, ("ONNX model", "*.onnx"))
                selected = filedialog.askopenfilename(title=f"Choose {label_text}", filetypes=filetypes)
                if selected:
                    variable.set(selected)

            tk.Button(row, text="Browse", command=browse, width=10).pack(side="left", padx=(8, 0))

        add_labeled_entry("Wake Phrase", wake_phrase_var)
        add_labeled_entry("Wake Model Name", wake_model_name_var)
        add_labeled_entry("Wake Model Path", wake_model_path_var, browse_kind="onnx")
        add_labeled_entry("Live2D Model Path", live2d_model_path_var, browse_kind="live2d")
        add_labeled_entry("TTS Voice", tts_voice_var)

        button_row = tk.Frame(container, bg="#f7efe7")
        button_row.pack(fill="x", pady=(20, 0))

        def save_and_close() -> None:
            data = asdict(config)
            data.update(
                enable_voice_pipeline=voice_enabled.get(),
                use_global_activity_hooks=hooks_enabled.get(),
                click_through_window=click_through_enabled.get(),
                wake_word_phrase=wake_phrase_var.get().strip() or config.wake_word_phrase,
                wake_word_model_name=wake_model_name_var.get().strip() or config.wake_word_model_name,
                wake_word_model_path=wake_model_path_var.get().strip(),
                live2d_model_path=live2d_model_path_var.get().strip(),
                edge_tts_voice=tts_voice_var.get().strip() or config.edge_tts_voice,
            )
            self._on_command(
                AppCommand(
                    name="save_settings",
                    payload={"config": AppConfig(**data), "autostart_enabled": autostart_var.get()},
                )
            )
            root.destroy()

        tk.Button(button_row, text="Save", command=save_and_close, width=12).pack(side="right")
        tk.Button(button_row, text="Cancel", command=root.destroy, width=12).pack(side="right", padx=(0, 8))

        def on_close() -> None:
            with self._lock:
                self._is_open = False
            root.destroy()

        root.protocol("WM_DELETE_WINDOW", on_close)
        try:
            root.mainloop()
        finally:
            with self._lock:
                self._is_open = False
