import json
import tempfile
import unittest
from pathlib import Path

from asset_analysis.notifications.message_builder import build_notification_message
from asset_analysis.pipeline import run_asset_pipeline


class NotificationMessageBuilderTests(unittest.TestCase):
    def test_dry_run_builds_notification_from_report_json(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            holdings = base / "holdings.yaml"
            output_dir = base / "reports"
            holdings.write_text('funds:\n  - code: "161725"\n    name: "Fund"\n    type: "fund"\n    cost_nav: 1.0\n    amount: 100\n    target_position: 1.0\n', encoding="utf-8")
            run_asset_pipeline(holdings, output_dir, data_source="mock", reporter_mode="offline")
            message = build_notification_message(output_dir / "report.json")
            self.assertEqual(message["title"], "Daily Asset Analysis")

    def test_message_includes_add_reduce_hold_counts(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            holdings = base / "holdings.yaml"
            output_dir = base / "reports"
            holdings.write_text('funds:\n  - code: "161725"\n    name: "Fund"\n    type: "fund"\n    cost_nav: 1.0\n    amount: 100\n    target_position: 1.0\n', encoding="utf-8")
            run_asset_pipeline(holdings, output_dir, data_source="mock", reporter_mode="offline")
            message = build_notification_message(output_dir / "report.json")
            self.assertIn("hold", message["signals_summary"])

    def test_message_includes_rule_based_limitation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            holdings = base / "holdings.yaml"
            output_dir = base / "reports"
            holdings.write_text('funds:\n  - code: "161725"\n    name: "Fund"\n    type: "fund"\n    cost_nav: 1.0\n    amount: 100\n    target_position: 1.0\n', encoding="utf-8")
            run_asset_pipeline(holdings, output_dir, data_source="mock", reporter_mode="offline")
            message = build_notification_message(output_dir / "report.json")
            self.assertIn("规则驱动", message["summary"])
