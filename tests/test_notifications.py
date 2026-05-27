import tempfile
import unittest
from pathlib import Path
from unittest import mock

from asset_analysis.notifications.registry import notify_from_report
from asset_analysis.pipeline import run_asset_pipeline


class NotificationTests(unittest.TestCase):
    def _build_report(self):
        temp_dir = tempfile.TemporaryDirectory()
        base = Path(temp_dir.name)
        holdings = base / "holdings.yaml"
        output_dir = base / "reports"
        holdings.write_text('funds:\n  - code: "161725"\n    name: "Fund"\n    type: "fund"\n    cost_nav: 1.0\n    amount: 100\n    target_position: 1.0\n', encoding="utf-8")
        run_asset_pipeline(holdings, output_dir, data_source="mock", reporter_mode="offline")
        return temp_dir, output_dir / "report.json"

    def test_missing_report_file_returns_structured_error(self):
        result = notify_from_report("missing_report.json", channel="dry_run")
        self.assertFalse(result["ok"])
        self.assertEqual(result["errors"][0]["stage"], "read_report")

    def test_dry_run_builds_notification_from_report_json(self):
        temp_dir, report = self._build_report()
        with temp_dir:
            result = notify_from_report(str(report), channel="dry_run")
            self.assertTrue(result["ok"])
            self.assertTrue(result["dry_run"])
            self.assertIn("signals_summary", result["message"])

    def test_missing_webhook_env_returns_config_error(self):
        temp_dir, report = self._build_report()
        with temp_dir:
            with mock.patch.dict("os.environ", {}, clear=True):
                result = notify_from_report(str(report), channel="webhook")
                self.assertFalse(result["ok"])
                self.assertEqual(result["errors"][0]["stage"], "config")

    def test_missing_email_env_returns_config_error(self):
        temp_dir, report = self._build_report()
        with temp_dir:
            with mock.patch.dict("os.environ", {}, clear=True):
                result = notify_from_report(str(report), channel="email")
                self.assertFalse(result["ok"])
                self.assertEqual(result["errors"][0]["stage"], "config")

    def test_missing_telegram_env_returns_config_error(self):
        temp_dir, report = self._build_report()
        with temp_dir:
            with mock.patch.dict("os.environ", {}, clear=True):
                result = notify_from_report(str(report), channel="telegram")
                self.assertFalse(result["ok"])
                self.assertEqual(result["errors"][0]["stage"], "config")

    def test_missing_discord_env_returns_config_error(self):
        temp_dir, report = self._build_report()
        with temp_dir:
            with mock.patch.dict("os.environ", {}, clear=True):
                result = notify_from_report(str(report), channel="discord")
                self.assertFalse(result["ok"])
                self.assertEqual(result["errors"][0]["stage"], "config")

    def test_network_send_functions_are_mockable(self):
        temp_dir, report = self._build_report()
        with temp_dir:
            with mock.patch.dict("os.environ", {"ASSET_ANALYSIS_WEBHOOK_URL": "https://example.test"}, clear=True):
                with mock.patch("asset_analysis.notifications.webhook.urlopen") as mocked:
                    mocked.return_value.__enter__.return_value = object()
                    result = notify_from_report(str(report), channel="webhook")
                    self.assertTrue(result["ok"])
                    mocked.assert_called_once()
