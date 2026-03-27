from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from queue import Empty, Queue
from threading import Event, Thread
from time import monotonic

import numpy as np
import sounddevice as sd

from core.speech_to_text import SpeechToTextService
from core.text_to_speech import TextToSpeechService
from core.wake_word import WakeWordDetector


@dataclass(slots=True)
class VoiceEvent:
    kind: str
    text: str = ""
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class VoicePipelineConfig:
    wake_word_phrase: str
    wake_word_model_name: str
    wake_word_model_path: Path | None
    wake_word_threshold: float
    sample_rate_hz: int
    chunk_size: int
    capture_max_seconds: float
    end_silence_seconds: float
    silence_rms_threshold: float
    whisper_model_size: str
    whisper_compute_type: str
    edge_tts_voice: str
    wake_models_dir: Path
    whisper_download_dir: Path


class VoicePipeline:
    def __init__(self, config: VoicePipelineConfig) -> None:
        self.config = config
        self._events: Queue[VoiceEvent] = Queue()
        self._audio_queue: Queue[np.ndarray] = Queue()
        self._tts_queue: Queue[str] = Queue()
        self._stop_event = Event()
        self._listener_thread: Thread | None = None
        self._tts_thread: Thread | None = None
        self._stream = None

        self.wake_word = WakeWordDetector(
            model_name=config.wake_word_model_name,
            threshold=config.wake_word_threshold,
            models_dir=config.wake_models_dir,
            custom_model_path=config.wake_word_model_path,
        )
        self.speech_to_text = SpeechToTextService(
            model_size=config.whisper_model_size,
            compute_type=config.whisper_compute_type,
            download_root=config.whisper_download_dir,
        )
        self.text_to_speech = TextToSpeechService(voice=config.edge_tts_voice)

    def start(self) -> VoiceEvent:
        status = self.wake_word.initialize()
        if not status.available:
            event = VoiceEvent(kind="voice_error", text=status.message)
            self._events.put(event)
            return event

        self._stream = sd.RawInputStream(
            samplerate=self.config.sample_rate_hz,
            channels=1,
            dtype="int16",
            blocksize=self.config.chunk_size,
            callback=self._audio_callback,
        )
        self._stream.start()
        self._listener_thread = Thread(target=self._listen_loop, name="nezuko-voice-listener", daemon=True)
        self._listener_thread.start()
        self._tts_thread = Thread(target=self._tts_loop, name="nezuko-voice-tts", daemon=True)
        self._tts_thread.start()
        event = VoiceEvent(
            kind="voice_status",
            text=f"Voice pipeline ready. Wake phrase target: {self.config.wake_word_phrase}.",
            metadata={"model": self.config.wake_word_model_name},
        )
        self._events.put(event)
        return event

    def stop(self) -> None:
        self._stop_event.set()
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None

    def poll_events(self) -> list[VoiceEvent]:
        events: list[VoiceEvent] = []
        while True:
            try:
                events.append(self._events.get_nowait())
            except Empty:
                return events

    def speak(self, text: str) -> None:
        if text.strip():
            self._tts_queue.put(text)

    def _audio_callback(self, indata, frames, time_info, status) -> None:
        del frames, time_info
        if status:
            self._events.put(VoiceEvent(kind="voice_error", text=str(status)))
        self._audio_queue.put(np.frombuffer(bytes(indata), dtype=np.int16).copy())

    def _listen_loop(self) -> None:
        capture_chunks: list[np.ndarray] = []
        capture_started = False
        last_voice_at = 0.0
        capture_started_at = 0.0

        while not self._stop_event.is_set():
            try:
                chunk = self._audio_queue.get(timeout=0.25)
            except Empty:
                continue

            if not capture_started:
                if self.wake_word.process_chunk(chunk):
                    capture_started = True
                    capture_chunks = []
                    capture_started_at = monotonic()
                    last_voice_at = capture_started_at
                    self._events.put(VoiceEvent(kind="wake_detected", text=self.config.wake_word_phrase))
                continue

            capture_chunks.append(chunk)
            rms = float(np.sqrt(np.mean((chunk.astype(np.float32) / 32768.0) ** 2)))
            now = monotonic()
            if rms >= self.config.silence_rms_threshold:
                last_voice_at = now

            elapsed = now - capture_started_at
            silence_elapsed = now - last_voice_at
            if elapsed < 0.35:
                continue

            if elapsed >= self.config.capture_max_seconds or silence_elapsed >= self.config.end_silence_seconds:
                capture_started = False
                audio = np.concatenate(capture_chunks) if capture_chunks else np.array([], dtype=np.int16)
                capture_chunks = []
                self._handle_captured_audio(audio)

    def _handle_captured_audio(self, audio: np.ndarray) -> None:
        if audio.size == 0:
            return
        try:
            transcript = self.speech_to_text.transcribe_pcm16(audio, self.config.sample_rate_hz)
        except Exception as exc:
            self._events.put(VoiceEvent(kind="voice_error", text=f"Transcription failed: {exc}"))
            return

        if transcript:
            self._events.put(VoiceEvent(kind="transcript", text=transcript))
        else:
            self._events.put(VoiceEvent(kind="transcript", text=""))

    def _tts_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                text = self._tts_queue.get(timeout=0.25)
            except Empty:
                continue
            try:
                self.text_to_speech.speak(text)
            except Exception as exc:
                self._events.put(VoiceEvent(kind="voice_error", text=f"TTS failed: {exc}"))
