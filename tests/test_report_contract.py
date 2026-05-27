import json
import tempfile
import unittest
from pathlib import Path

from asset_analysis.hermes_adapter import run_daily_asset_analysis_task
from asset_analysis.openclaw_adapter import run_asset_analysis_skill
from asset_analysis.pipeline import run_asset_pipeline
from asset_analysis.schema.constants import ASSET_ANALYSIS_SCHEMA_VERSION


class ReportContractTests(unittest.TestCase):
    def test_pipeline_report_includes_schema_fields(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            holdings = base / "holdings.yaml"
            output_dir = base / "reports"
            holdings.write_text('funds:\n  - code: "161725"\n    name: "Fund"\n    type: "fund"\n    cost_nav: 1.0\n    amount: 100\n    target_position: 1.0\n', encoding="utf-8")
            run_asset_pipeline(holdings, output_dir, data_source="mock", reporter_mode="offline")
            payload = json.loads((output_dir / "report.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["schema_version"], ASSET_ANALYSIS_SCHEMA_VERSION)
            self.assertIn("generated_at", payload)
            self.assertIn("run", payload)
            self.assertIn("schema_errors", payload)

    def test_openclaw_result_includes_schema_fields(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            holdings = base / "holdings.yaml"
            output_dir = base / "reports"
            holdings.write_text('funds:\n  - code: "161725"\n    name: "Fund"\n    type: "fund"\n    cost_nav: 1.0\n    amount: 100\n    target_position: 1.0\n', encoding="utf-8")
            result = run_asset_analysis_skill(str(holdings), str(output_dir))
            self.assertEqual(result["schema_version"], ASSET_ANALYSIS_SCHEMA_VERSION)
            self.assertIn("generated_at", result)
            self.assertIn("schema_errors", result)

    def test_hermes_result_includes_schema_fields(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            holdings = base / "holdings.yaml"
            output_dir = base / "reports"
            holdings.write_text('funds:\n  - code: "161725"\n    name: "Fund"\n    type: "fund"\n    cost_nav: 1.0\n    amount: 100\n    target_position: 1.0\n', encoding="utf-8")
            result = run_daily_asset_analysis_task(holdings_path=str(holdings), output_dir=str(output_dir))
            self.assertEqual(result["schema_version"], ASSET_ANALYSIS_SCHEMA_VERSION)
            self.assertIn("generated_at", result)
            self.assertIn("schema_errors", result)

    def test_run_json_is_generated(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            holdings = base / "holdings.yaml"
            output_dir = base / "reports"
            holdings.write_text('funds:\n  - code: "161725"\n    name: "Fund"\n    type: "fund"\n    cost_nav: 1.0\n    amount: 100\n    target_position: 1.0\n', encoding="utf-8")
            run_asset_pipeline(holdings, output_dir, data_source="mock", reporter_mode="offline")
            self.assertTrue((output_dir / "run.json").exists())

    def test_latest_run_json_is_generated_when_output_is_under_reports(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            holdings = base / "holdings.yaml"
            reports_root = base / "reports"
            output_dir = reports_root / "demo"
            holdings.write_text('funds:\n  - code: "161725"\n    name: "Fund"\n    type: "fund"\n    cost_nav: 1.0\n    amount: 100\n    target_position: 1.0\n', encoding="utf-8")
            run_asset_pipeline(holdings, output_dir, data_source="mock", reporter_mode="offline")
            self.assertTrue((reports_root / "latest_run.json").exists())

    def test_archive_mode_writes_timestamped_copies(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            holdings = base / "holdings.yaml"
            reports_root = base / "reports"
            output_dir = reports_root / "demo"
            holdings.write_text('funds:\n  - code: "161725"\n    name: "Fund"\n    type: "fund"\n    cost_nav: 1.0\n    amount: 100\n    target_position: 1.0\n', encoding="utf-8")
            run_asset_pipeline(holdings, output_dir, data_source="mock", reporter_mode="offline", archive=True)
            archive_root = reports_root / "archive"
            self.assertTrue(archive_root.exists())
