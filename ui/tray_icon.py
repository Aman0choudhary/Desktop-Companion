from __future__ import annotations

from typing import Callable

from core.commands import AppCommand
from core.status import AppStatusStore


class TrayIconController:
    def __init__(self, status_store: AppStatusStore, on_command: Callable[[AppCommand], None]) -> None:
        self._status_store = status_store
        self._on_command = on_command
        self._icon = None
        self._pystray = None

    def start(self) -> bool:
        if self._icon is not None:
            return True

        try:
            import pystray
            from PIL import Image, ImageDraw
        except Exception:
            return False

        self._pystray = pystray
        icon_image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(icon_image)
        draw.ellipse((6, 6, 58, 58), fill=(43, 48, 53, 255), outline=(244, 114, 96, 255), width=4)
        draw.rectangle((22, 24, 42, 40), fill=(255, 173, 96, 255))
        draw.rectangle((28, 18, 36, 24), fill=(244, 114, 96, 255))

        self._icon = pystray.Icon(
            "nezuko-desktop-companion",
            icon_image,
            "Nezuko Desktop Companion",
            self._build_menu(),
        )
        self._icon.run_detached()
        return True

    def stop(self) -> None:
        if self._icon is None:
            return
        try:
            self._icon.stop()
        except Exception:
            pass
        self._icon = None

    def refresh(self) -> None:
        if self._icon is not None:
            self._icon.update_menu()

    def _build_menu(self):
        pystray = self._pystray
        return pystray.Menu(
            pystray.MenuItem("Open Settings", self._emit_show_settings, default=True),
            pystray.MenuItem("Do Not Disturb", self._emit_toggle_dnd, checked=lambda _item: self._status_store.snapshot().dnd_enabled),
            pystray.MenuItem("Voice Pipeline", self._emit_toggle_voice, checked=lambda _item: self._status_store.snapshot().voice_enabled),
            pystray.MenuItem(
                "Click Through",
                self._emit_toggle_click_through,
                checked=lambda _item: self._status_store.snapshot().click_through_enabled,
            ),
            pystray.MenuItem(
                "Start With Windows",
                self._emit_toggle_autostart,
                checked=lambda _item: self._status_store.snapshot().autostart_enabled,
            ),
            pystray.MenuItem(lambda _item: f"Active Model: {self._status_store.snapshot().active_model_name}", None, enabled=False),
            pystray.MenuItem("Quit", self._emit_quit),
        )

    def _emit(self, name: str) -> None:
        self._on_command(AppCommand(name=name))

    def _emit_show_settings(self, icon, item) -> None:
        del icon, item
        self._emit("show_settings")

    def _emit_toggle_dnd(self, icon, item) -> None:
        del icon, item
        self._emit("toggle_dnd")

    def _emit_toggle_voice(self, icon, item) -> None:
        del icon, item
        self._emit("toggle_voice")

    def _emit_toggle_click_through(self, icon, item) -> None:
        del icon, item
        self._emit("toggle_click_through")

    def _emit_toggle_autostart(self, icon, item) -> None:
        del icon, item
        self._emit("toggle_autostart")

    def _emit_quit(self, icon, item) -> None:
        del icon, item
        self._emit("quit")
