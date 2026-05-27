import json
import tempfile
import unittest
from pathlib import Path

from asset_analysis.classification.group_config import load_portfolio_template
from asset_analysis.notifications.message_builder import build_notification_message
from asset_analysis.pipeline import run_asset_pipeline


class PortfolioTemplateTests(unittest.TestCase):
    def test_pipeline_accepts_asset_groups(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            holdings = base / "holdings.yaml"
            groups = base / "groups.yaml"
            output_dir = base / "reports"
            holdings.write_text('funds:\n  - code: "161725"\n    name: "招商中证白酒指数(LOF)A"\n    type: "fund"\n    cost_nav: 1.0\n    amount: 100\n    target_position: 1.0\n', encoding="utf-8")
            groups.write_text('mappings:\n  "161725":\n    group: sector_theme\n    tags: ["白酒"]\n', encoding="utf-8")
            result = run_asset_pipeline(holdings, output_dir, data_source="mock", reporter_mode="offline", asset_groups_path=groups)
            self.assertEqual(result.positions[0].group, "sector_theme")

    def test_pipeline_accepts_portfolio_template(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            holdings = base / "holdings.yaml"
            groups = base / "groups.yaml"
            template = base / "template.yaml"
            output_dir = base / "reports"
            holdings.write_text('funds:\n  - code: "161725"\n    name: "招商中证白酒指数(LOF)A"\n    type: "fund"\n    cost_nav: 1.0\n    amount: 100\n    target_position: 1.0\n', encoding="utf-8")
            groups.write_text('mappings:\n  "161725":\n    group: sector_theme\n    tags: ["白酒"]\n', encoding="utf-8")
            template.write_text('groups:\n  sector_theme:\n    target_position: 0.2\n    max_position: 0.3\n', encoding="utf-8")
            result = run_asset_pipeline(holdings, output_dir, data_source="mock", reporter_mode="offline", asset_groups_path=groups, portfolio_template_path=template)
            self.assertTrue(result.group_analysis["warnings"])

    def test_report_json_includes_group_analysis(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            holdings = base / "holdings.yaml"
            output_dir = base / "reports"
            holdings.write_text('funds:\n  - code: "161725"\n    name: "招商中证白酒指数(LOF)A"\n    type: "fund"\n    cost_nav: 1.0\n    amount: 100\n    target_position: 1.0\n', encoding="utf-8")
            run_asset_pipeline(holdings, output_dir, data_source="mock", reporter_mode="offline")
            payload = json.loads((output_dir / "report.json").read_text(encoding="utf-8"))
            self.assertIn("group_analysis", payload)

    def test_notification_message_includes_group_warning_summary_if_present(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            holdings = base / "holdings.yaml"
            groups = base / "groups.yaml"
            template = base / "template.yaml"
            output_dir = base / "reports"
            holdings.write_text('funds:\n  - code: "161725"\n    name: "招商中证白酒指数(LOF)A"\n    type: "fund"\n    cost_nav: 1.0\n    amount: 100\n    target_position: 1.0\n', encoding="utf-8")
            groups.write_text('mappings:\n  "161725":\n    group: sector_theme\n    tags: ["白酒"]\n', encoding="utf-8")
            template.write_text('groups:\n  sector_theme:\n    target_position: 0.2\n    max_position: 0.3\n', encoding="utf-8")
            run_asset_pipeline(holdings, output_dir, data_source="mock", reporter_mode="offline", asset_groups_path=groups, portfolio_template_path=template)
            message = build_notification_message(output_dir / "report.json")
            self.assertIn("分组风险提醒", message["summary"])
