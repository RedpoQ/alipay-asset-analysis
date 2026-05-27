import json
import tempfile
import unittest
from pathlib import Path

from asset_analysis.pipeline import main as pipeline_main
from asset_analysis.quotes.data_quality import build_data_quality
from asset_analysis.models import AssetPosition


class DataQualityTests(unittest.TestCase):
    def test_pipeline_accepts_manual_quotes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            holdings = base / "holdings.yaml"
            output_dir = base / "reports"
            holdings.write_text(Path("examples/real_existing_holdings.yaml").read_text(encoding="utf-8"), encoding="utf-8")
            code = pipeline_main(
                [
                    "--input",
                    str(holdings),
                    "--output",
                    str(output_dir),
                    "--data-source",
                    "manual",
                    "--quotes",
                    "examples/manual_quotes.example.csv",
                    "--reporter",
                    "offline",
                ]
            )
            self.assertEqual(code, 0)
            payload = json.loads((output_dir / "report.json").read_text(encoding="utf-8"))
            self.assertIn("data_quality", payload)
            self.assertEqual(payload["data_quality"]["analysis_scope"], "manual_quote")

    def test_old_pipeline_command_still_works(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            holdings = base / "holdings.yaml"
            output_dir = base / "reports"
            holdings.write_text(Path("examples/real_existing_holdings.yaml").read_text(encoding="utf-8"), encoding="utf-8")
            code = pipeline_main(
                [
                    "--input",
                    str(holdings),
                    "--output",
                    str(output_dir),
                    "--data-source",
                    "mock",
                    "--reporter",
                    "offline",
                ]
            )
            self.assertEqual(code, 0)

    def test_data_quality_builder_counts_missing_quotes(self):
        positions = [
            AssetPosition(
                code="000001",
                name="华夏成长混合",
                type="fund",
                cost=100,
                market_value=100,
                profit=0,
                profit_rate=0,
                target_position=0.2,
                current_position=0.2,
                quote={"source": "manual_missing", "error": {"code": "MANUAL_QUOTE_MISSING"}, "freshness": {"status": "unknown"}},
            )
        ]
        quality = build_data_quality("manual", positions)
        self.assertEqual(quality["missing_quote_count"], 1)
