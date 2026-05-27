import tempfile
import unittest
from pathlib import Path

from asset_analysis.notifications.config import load_notification_config


class NotificationConfigTests(unittest.TestCase):
    def test_default_config_loads_dry_run_only(self):
        config = load_notification_config()
        self.assertEqual(len(config.channels), 1)
        self.assertEqual(config.channels[0].name, "dry_run")
        self.assertTrue(config.channels[0].enabled)

    def test_yaml_config_loads(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "notify.yaml"
            path.write_text(
                "channels:\n  - name: dry_run\n    enabled: true\nrouting:\n  default_channels:\n    - dry_run\n",
                encoding="utf-8",
            )
            config = load_notification_config(str(path))
            self.assertEqual(config.routing.default_channels, ["dry_run"])

    def test_unknown_channel_produces_config_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "notify.yaml"
            path.write_text(
                "channels:\n  - name: unknown\n    enabled: true\n",
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                load_notification_config(str(path))
