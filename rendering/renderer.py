from __future__ import annotations

import os
from dataclasses import dataclass
from time import monotonic
from typing import Callable

import pygame

from core.state_machine import NezukoState
from rendering.animations import AnimationFrame
from rendering.model_controller import ModelController
from rendering.roam_engine import CharacterPose
from rendering.window_effects import configure_overlay_window, move_overlay_window


@dataclass(slots=True)
class DrawPalette:
    background_key: tuple[int, int, int] = (255, 0, 255)
    body: tuple[int, int, int] = (22, 26, 29)
    outline: tuple[int, int, int] = (0, 0, 0)
    scarf: tuple[int, int, int] = (249, 65, 68)
    eyes: tuple[int, int, int] = (255, 255, 255)
    text: tuple[int, int, int] = (248, 249, 250)
    bubble_fill: tuple[int, int, int] = (255, 248, 231)
    bubble_text: tuple[int, int, int] = (16, 20, 24)


class DesktopRenderer:
    def __init__(
        self,
        width: int,
        height: int,
        bubble_duration_seconds: float,
        on_key: Callable[[str], None] | None = None,
        on_command: Callable[[str], None] | None = None,
        click_through: bool = True,
        model_path: str | None = None,
    ) -> None:
        self.width = width
        self.height = height
        self._on_key = on_key
        self._on_command = on_command
        self._close_requested = False
        self._bubble_duration_seconds = bubble_duration_seconds
        self._bubble_text = ""
        self._bubble_expires_at = 0.0
        self._command_buffer = ""
        self._command_mode = False
        self.palette = DrawPalette()
        self.model_controller = ModelController(model_path=model_path)
        self._uses_opengl = self.model_controller.supports_live2d()
        self._click_through = click_through
        self._window_x = 40
        self._window_y = 40

        os.environ.setdefault("SDL_VIDEO_WINDOW_POS", "40,40")
        pygame.init()
        pygame.font.init()

        flags = pygame.NOFRAME | pygame.DOUBLEBUF
        if self._uses_opengl:
            flags |= pygame.OPENGL

        self.screen = pygame.display.set_mode((width, height), flags)
        pygame.display.set_caption("Nezuko Prototype")
        self._font = pygame.font.SysFont("Segoe UI", 16)
        self._small_font = pygame.font.SysFont("Segoe UI", 12, bold=True)
        self._clock = pygame.time.Clock()
        self._window_handle = pygame.display.get_wm_info().get("window", 0)

        configure_overlay_window(
            self._window_handle,
            x=self._window_x,
            y=self._window_y,
            width=width,
            height=height,
            click_through=click_through,
            colorkey_rgb=self.palette.background_key,
        )
        status = self.model_controller.initialize(width, height) if self._uses_opengl else self.model_controller.status()
        self.show_bubble(status.message if status.available else "Phase 1 window online. Add a Live2D model to assets/live2d/.")

    def get_screen_size(self) -> tuple[int, int]:
        info = pygame.display.Info()
        return info.current_w, info.current_h

    def show_bubble(self, text: str) -> None:
        self._bubble_text = text
        self._bubble_expires_at = monotonic() + self._bubble_duration_seconds

    def active_model_name(self) -> str:
        return self.model_controller.model_name()

    def set_click_through(self, enabled: bool) -> None:
        self._click_through = enabled
        configure_overlay_window(
            self._window_handle,
            x=self._window_x,
            y=self._window_y,
            width=self.width,
            height=self.height,
            click_through=enabled,
            colorkey_rgb=self.palette.background_key,
        )

    def open_command_input(self) -> None:
        self._command_mode = True
        self._command_buffer = ""

    def render(self, pose: CharacterPose, frame: AnimationFrame, state: NezukoState) -> None:
        self._pump_events()
        self._window_x = int(pose.x)
        self._window_y = int(pose.y + frame.bob_offset)
        move_overlay_window(self._window_handle, self._window_x, self._window_y, self.width, self.height)

        if self._uses_opengl:
            self.model_controller.update_for_pose(
                state=state,
                facing_right=pose.facing_right,
                bob_offset=frame.bob_offset,
                opacity=pose.opacity,
            )
            self.model_controller.draw()
            pygame.display.flip()
            return

        self.screen.fill(self.palette.background_key)
        self._draw_placeholder(frame=frame, pose=pose, state_label=state.value)
        self._draw_bubble()
        self._draw_command_prompt()
        pygame.display.flip()

    def request_close(self) -> None:
        self._close_requested = True
        self.model_controller.shutdown()
        pygame.quit()

    def run(self, tick: Callable[[], None], interval_ms: int) -> None:
        target_fps = max(1, int(1000 / max(1, interval_ms)))
        while not self._close_requested:
            tick()
            self._clock.tick(target_fps)
        self.model_controller.shutdown()

    def _pump_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.request_close()
                continue
            if event.type != pygame.KEYDOWN:
                continue
            if event.key == pygame.K_ESCAPE:
                if self._command_mode:
                    self._command_mode = False
                    self._command_buffer = ""
                elif self._on_key is not None:
                    self._on_key("Escape")
                continue

            if self._command_mode:
                self._handle_command_key(event)
                continue

            if event.key == pygame.K_RETURN:
                self.open_command_input()
                continue

            if self._on_key is not None:
                self._on_key(pygame.key.name(event.key))

    def _handle_command_key(self, event: pygame.event.Event) -> None:
        if event.key == pygame.K_RETURN:
            text = self._command_buffer.strip()
            self._command_mode = False
            self._command_buffer = ""
            if text and self._on_command is not None:
                self._on_command(text)
            return
        if event.key == pygame.K_BACKSPACE:
            self._command_buffer = self._command_buffer[:-1]
            return
        if event.unicode and event.unicode.isprintable():
            self._command_buffer += event.unicode

    def _draw_placeholder(self, frame: AnimationFrame, pose: CharacterPose, state_label: str) -> None:
        center_x = self.width // 2
        head_rect = pygame.Rect(center_x - 60, 28, 120, 120)
        body_rect = pygame.Rect(center_x - 72, 116, 144, self.height - 142)

        pygame.draw.ellipse(self.screen, frame.accent_color, head_rect)
        pygame.draw.ellipse(self.screen, self.palette.outline, head_rect, width=3)
        pygame.draw.rect(self.screen, self.palette.body, body_rect)
        pygame.draw.rect(self.screen, self.palette.outline, body_rect, width=3)
        pygame.draw.rect(self.screen, self.palette.scarf, pygame.Rect(center_x - 75, 134, 150, 24))
        pygame.draw.rect(self.screen, self.palette.outline, pygame.Rect(center_x - 75, 134, 150, 24), width=2)

        eye_height = 10 if frame.eye_open else 2
        for eye_x in (center_x - 24, center_x + 24):
            eye_rect = pygame.Rect(eye_x - 9, 90 - (eye_height // 2), 18, eye_height)
            pygame.draw.ellipse(self.screen, self.palette.eyes, eye_rect)
            pygame.draw.ellipse(self.screen, self.palette.outline, eye_rect, width=2)

        mouth_y = 120 if frame.eye_open else 116
        mouth_span = 18 if frame.mood_label != "sleep" else 10
        pygame.draw.line(self.screen, self.palette.outline, (center_x - mouth_span, mouth_y), (center_x + mouth_span, mouth_y), width=3)

        direction = "right" if pose.facing_right else "left"
        label = self._small_font.render(f"{state_label} | facing {direction}", True, self.palette.text)
        self.screen.blit(label, label.get_rect(center=(center_x, self.height - 18)))

    def _draw_bubble(self) -> None:
        if not self._bubble_text or monotonic() >= self._bubble_expires_at:
            return
        rect = pygame.Rect(8, 8, self.width - 16, 54)
        pygame.draw.rect(self.screen, self.palette.bubble_fill, rect, border_radius=18)
        pygame.draw.rect(self.screen, self.palette.outline, rect, width=2, border_radius=18)
        bubble_text = self._font.render(self._bubble_text[:60], True, self.palette.bubble_text)
        self.screen.blit(bubble_text, bubble_text.get_rect(center=rect.center))

    def _draw_command_prompt(self) -> None:
        if not self._command_mode:
            return
        rect = pygame.Rect(10, self.height - 56, self.width - 20, 36)
        pygame.draw.rect(self.screen, self.palette.bubble_fill, rect, border_radius=12)
        pygame.draw.rect(self.screen, self.palette.outline, rect, width=2, border_radius=12)
        prompt = self._font.render(f"> {self._command_buffer}", True, self.palette.bubble_text)
        self.screen.blit(prompt, (rect.x + 8, rect.y + 8))
