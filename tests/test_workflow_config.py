import tempfile
import unittest
from pathlib import Path

from asset_analysis.workflow.config import load_workflow_config


class WorkflowConfigTests(unittest.TestCase):
    def test_config_example_loads(self):
        config = load_workflow_config("private/config.local.example.yaml")
        self.assertEqual(config.input.mode, "alipay_csv")
        self.assertEqual(config.analysis.reporter, "offline")
        self.assertTrue(config.preflight.enabled)

    def test_invalid_mode_raises_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "config.yaml"
            path.write_text("input:\n  mode: bad_mode\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                load_workflow_config(path)
