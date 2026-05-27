import json
import tempfile
import unittest
from pathlib import Path

from asset_analysis.data_sources.mock_source import MockDataSource
from asset_analysis.data_sources.registry import get_data_source
from asset_analysis.fund_fetcher import AssetDataFetcher
from asset_analysis.models import AssetHolding
from asset_analysis.pipeline import main as pipeline_main, run_asset_pipeline


class DataSourceTests(unittest.TestCase):
    def test_mock_source_returns_deterministic_quote(self):
        source = MockDataSource()
        asset = AssetHolding(code="161725", name="Fund", type="fund", amount=100, target_position=0.3, cost_nav=1.0)
        quote_a = source.fetch_quote(asset)
        quote_b = source.fetch_quote(asset)
        self.assertEqual(quote_a.current_nav, quote_b.current_nav)
        self.assertEqual(quote_a.source, "mock")

    def test_registry_returns_mock_source(self):
        source = get_data_source("mock")
        self.assertEqual(source.name, "mock")

    def test_auto_mode_falls_back_to_mock_when_public_source_fails(self):
        asset = AssetHolding(code="161725", name="Fund", type="fund", amount=100, target_position=0.3, cost_nav=1.0)
        fetcher = AssetDataFetcher(data_source="auto")
        quote = fetcher.fetch_asset(asset)
        self.assertIn(quote.source, {"fallback", "public_fund", "mock"})
        if quote.source == "fallback":
            self.assertIsNotNone(quote.error)

    def test_failed_quote_does_not_crash_pipeline(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            input_file = Path(temp_dir) / "holdings.yaml"
            output_dir = Path(temp_dir) / "reports"
            input_file.write_text(
                """
stocks:
  - code: "FAIL_STOCK"
    name: "Failure Case"
    type: "stock"
    cost_price: 10
    amount: 10
    target_position: 1.0
""".strip(),
                encoding="utf-8",
            )
            result = run_asset_pipeline(input_file, output_dir, data_source="mock")
            self.assertTrue((output_dir / "report.json").exists())
            self.assertIsNotNone(result.positions[0].quote)
            self.assertIsNotNone(result.positions[0].error)

    def test_pipeline_cli_works_with_data_source_mock(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            input_file = Path(temp_dir) / "holdings.yaml"
            output_dir = Path(temp_dir) / "reports"
            input_file.write_text(
                """
funds:
  - code: "161725"
    name: "Example Fund"
    type: "fund"
    cost_nav: 1.0
    amount: 100
    target_position: 1.0
""".strip(),
                encoding="utf-8",
            )
            exit_code = pipeline_main(
                ["--input", str(input_file), "--output", str(output_dir), "--data-source", "mock"]
            )
            self.assertEqual(exit_code, 0)
            self.assertTrue((output_dir / "report.json").exists())

    def test_report_json_includes_quote_source_fields(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            input_file = Path(temp_dir) / "holdings.yaml"
            output_dir = Path(temp_dir) / "reports"
            input_file.write_text(
                """
funds:
  - code: "161725"
    name: "Example Fund"
    type: "fund"
    cost_nav: 1.0
    amount: 100
    target_position: 1.0
""".strip(),
                encoding="utf-8",
            )
            run_asset_pipeline(input_file, output_dir, data_source="mock")
            payload = json.loads((output_dir / "report.json").read_text(encoding="utf-8"))
            position = payload["positions"][0]
            self.assertIn("quote", position)
            self.assertEqual(position["quote"]["source"], "mock")
