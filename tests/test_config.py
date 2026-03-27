import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.config import AppConfig, load_app_config, save_app_config


class ConfigTests(unittest.TestCase):
    def test_load_returns_defaults_when_file_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("core.config.config_root", return_value=Path(temp_dir)):
                config = load_app_config()
        self.assertEqual(config.wake_word_phrase, "Hey Nezuko")

    def test_save_and_load_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("core.config.config_root", return_value=Path(temp_dir)):
                config = AppConfig(click_through_window=False, live2d_model_path="assets/live2d/nezuko.model3.json")
                save_app_config(config)
                loaded = load_app_config()
        self.assertFalse(loaded.click_through_window)
        self.assertEqual(loaded.live2d_model_path, "assets/live2d/nezuko.model3.json")


if __name__ == "__main__":
    unittest.main()
