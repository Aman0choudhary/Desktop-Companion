import tempfile
import unittest
from pathlib import Path

from rendering.model_controller import ModelController


class ModelControllerTests(unittest.TestCase):
    def test_find_default_model_path_prefers_model3_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            model_dir = root / "assets" / "live2d" / "nezuko"
            model_dir.mkdir(parents=True, exist_ok=True)
            model_path = model_dir / "nezuko.model3.json"
            model_path.write_text("{}", encoding="utf-8")

            discovered = ModelController.find_default_model_path(root)
            self.assertEqual(discovered, model_path)

    def test_resolve_model_path_accepts_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            model_dir = root / "custom-model"
            model_dir.mkdir(parents=True, exist_ok=True)
            model_path = model_dir / "nezuko.model3.json"
            model_path.write_text("{}", encoding="utf-8")

            resolved = ModelController.resolve_model_path(model_dir)
            self.assertEqual(resolved, model_path)

    def test_status_without_model_reports_missing_asset(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            controller = ModelController(model_path=Path(temp_dir) / "missing.model3.json")
            status = controller.status()
            self.assertFalse(status.available)
            self.assertFalse(status.loaded)


if __name__ == "__main__":
    unittest.main()
