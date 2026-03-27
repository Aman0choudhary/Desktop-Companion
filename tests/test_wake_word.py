import tempfile
import unittest
from pathlib import Path

from core.speech_to_text import SpeechToTextService
from core.text_to_speech import TextToSpeechService
from core.wake_word import WakeWordDetector


class VoiceServiceTests(unittest.TestCase):
    def test_wake_word_reports_missing_model(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            detector = WakeWordDetector(
                model_name="hey_jarvis",
                threshold=0.5,
                models_dir=Path(temp_dir),
            )
            status = detector.initialize()
            self.assertFalse(status.available)
            self.assertIn("missing", status.message.lower())

    def test_custom_wake_word_path_is_checked(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            detector = WakeWordDetector(
                model_name="hey_jarvis",
                threshold=0.5,
                models_dir=Path(temp_dir),
                custom_model_path=Path(temp_dir) / "hey_nezuko.onnx",
            )
            status = detector.initialize()
            self.assertFalse(status.available)
            self.assertIn("hey_nezuko.onnx", status.message)

    def test_speech_to_text_status_is_lazy(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = SpeechToTextService(
                model_size="tiny.en",
                compute_type="int8",
                download_root=Path(temp_dir),
            )
            status = service.status()
            self.assertFalse(status.ready)
            self.assertIn("not loaded", status.message.lower())

    def test_text_to_speech_status_reports_voice(self) -> None:
        service = TextToSpeechService(voice="en-IN-NeerjaNeural")
        status = service.status()
        self.assertTrue(status.available)
        self.assertIn("Neerja", status.message)


if __name__ == "__main__":
    unittest.main()
