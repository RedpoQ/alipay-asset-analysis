import tempfile
import unittest
from pathlib import Path
from unittest import mock

from asset_analysis.notifications.orchestrator import run_notification_orchestrator
from asset_analysis.pipeline import run_asset_pipeline


class NotificationOrchestratorTests(unittest.TestCase):
    def _build_report(self):
        temp_dir = tempfile.TemporaryDirectory()
        base = Path(temp_dir.name)
        holdings = base / "holdings.yaml"
        output_dir = base / "reports"
        holdings.write_text(
            'funds:\n  - code: "000001"\n    name: "Fund1"\n    type: "fund"\n    cost_nav: 1.0\n    amount: 100\n    target_position: 0.25\n  - code: "110022"\n    name: "Fund2"\n    type: "fund"\n    cost_nav: 2.0\n    amount: 200\n    target_position: 0.30\n',
            encoding="utf-8",
        )
        run_asset_pipeline(holdings, output_dir, data_source="mock", reporter_mode="offline")
        return temp_dir, output_dir / "report.json"

    def test_orchestrator_dry_run_sends_only_dry_run(self):
        temp_dir, report = self._build_report()
        with temp_dir:
            result = run_notification_orchestrator(str(report), dry_run=True)
            self.assertTrue(result["ok"])
            self.assertEqual(result["selected_channels"], ["dry_run"])

    def test_explicit_channels_override_config(self):
        temp_dir, report = self._build_report()
        with temp_dir:
            result = run_notification_orchestrator(str(report), channels=["dry_run"], dry_run=True)
            self.assertEqual(result["selected_channels"], ["dry_run"])

    def test_one_channel_failure_does_not_prevent_another_channel(self):
        temp_dir, report = self._build_report()
        with temp_dir:
            config_path = Path(temp_dir.name) / "notify.yaml"
            config_path.write_text(
                "channels:\n  - name: dry_run\n    enabled: true\n  - name: webhook\n    enabled: true\nrouting:\n  default_channels:\n    - dry_run\n    - webhook\nsafety:\n  dry_run_default: false\n  allow_network_channels: true\n",
                encoding="utf-8",
            )
            with mock.patch("asset_analysis.notifications.webhook.urlopen", side_effect=OSError("boom")):
                result = run_notification_orchestrator(str(report), config_path=str(config_path), dry_run=False)
            self.assertTrue(result["ok"])
            self.assertEqual(result["summary"]["succeeded"], 1)

    def test_all_channel_failures_returns_ok_false(self):
        temp_dir, report = self._build_report()
        with temp_dir:
            config_path = Path(temp_dir.name) / "notify.yaml"
            config_path.write_text(
                "channels:\n  - name: webhook\n    enabled: true\nrouting:\n  default_channels:\n    - webhook\nsafety:\n  dry_run_default: false\n  allow_network_channels: true\n",
                encoding="utf-8",
            )
            with mock.patch("asset_analysis.notifications.webhook.urlopen", side_effect=OSError("boom")):
                result = run_notification_orchestrator(str(report), config_path=str(config_path), dry_run=False)
            self.assertFalse(result["ok"])

    def test_retry_attempts_are_counted(self):
        temp_dir, report = self._build_report()
        with temp_dir:
            config_path = Path(temp_dir.name) / "notify.yaml"
            config_path.write_text(
                "channels:\n  - name: webhook\n    enabled: true\n    retry:\n      max_attempts: 2\n      backoff_seconds: 0\nrouting:\n  default_channels:\n    - webhook\nsafety:\n  dry_run_default: false\n  allow_network_channels: true\n",
                encoding="utf-8",
            )
            with mock.patch("asset_analysis.notifications.webhook.urlopen", side_effect=OSError("boom")):
                result = run_notification_orchestrator(str(report), config_path=str(config_path), dry_run=False)
            self.assertEqual(result["results"][0]["attempts"], 2)

    def test_dry_run_true_prevents_network_channels(self):
        temp_dir, report = self._build_report()
        with temp_dir:
            config_path = Path(temp_dir.name) / "notify.yaml"
            config_path.write_text(
                "channels:\n  - name: webhook\n    enabled: true\nrouting:\n  default_channels:\n    - webhook\nsafety:\n  dry_run_default: true\n  allow_network_channels: true\n",
                encoding="utf-8",
            )
            result = run_notification_orchestrator(str(report), config_path=str(config_path), dry_run=True)
            self.assertFalse(result["ok"])
            self.assertEqual(result["summary"]["skipped"], 1)
