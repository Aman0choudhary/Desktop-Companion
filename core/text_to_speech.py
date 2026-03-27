from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile

import pygame


@dataclass(slots=True)
class TextToSpeechStatus:
    available: bool
    message: str


class TextToSpeechService:
    def __init__(self, voice: str) -> None:
        self.voice = voice

    def status(self) -> TextToSpeechStatus:
        return TextToSpeechStatus(
            available=True,
            message=f"TTS ready with voice '{self.voice}'.",
        )

    def speak(self, text: str) -> None:
        if not text.strip():
            return
        with NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
            target = Path(temp_file.name)
        try:
            asyncio.run(self._synthesize(text, target))
            self._play_file(target)
        finally:
            target.unlink(missing_ok=True)

    async def _synthesize(self, text: str, target: Path) -> None:
        import edge_tts

        communicate = edge_tts.Communicate(text, voice=self.voice)
        await communicate.save(str(target))

    def _play_file(self, target: Path) -> None:
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        pygame.mixer.music.load(str(target))
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.wait(50)
