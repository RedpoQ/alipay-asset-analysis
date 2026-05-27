import tempfile
import unittest
from pathlib import Path

from asset_analysis.rules.config import load_rule_config


class RulesConfigTests(unittest.TestCase):
    def test_default_rules_config_loads(self):
        config, source = load_rule_config()
        self.assertEqual(source, "default")
        self.assertAlmostEqual(config.portfolio.max_single_position, 0.35)

    def test_yaml_rules_config_loads(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "rules.yaml"
            path.write_text(
                "portfolio:\n  max_single_position: 0.4\nposition:\n  rebalance_band: 0.06\n",
                encoding="utf-8",
            )
            config, source = load_rule_config(path)
            self.assertEqual(source, str(path))
            self.assertAlmostEqual(config.portfolio.max_single_position, 0.4)
            self.assertAlmostEqual(config.position.rebalance_band, 0.06)

    def test_invalid_config_raises_readable_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "rules.yaml"
            path.write_text("portfolio:\n  max_single_position:\n    - bad\n", encoding="utf-8")
            with self.assertRaises(ValueError) as context:
                load_rule_config(path)
            self.assertIn("Invalid rules config fields", str(context.exception))
