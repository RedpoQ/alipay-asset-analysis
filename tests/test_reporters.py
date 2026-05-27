import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from asset_analysis.models import AnalysisSummary, AssetAnalysisResult, AssetPosition, SignalResult
from asset_analysis.pipeline import main as pipeline_main, run_asset_pipeline
from asset_analysis.reporters.llm_reporter import LLMReporter
from asset_analysis.reporters.offline_reporter import OfflineReporter
from asset_analysis.reporters.registry import get_reporter


def _sample_result():
    return AssetAnalysisResult(
        summary=AnalysisSummary(100, 105, 5, 0.05),
        positions=[AssetPosition(code="161725", name="Fund", type="fund", cost=100, market_value=105, profit=5, profit_rate=0.05, target_position=0.5, current_position=0.5, quote={"source": "mock", "as_of": "2026-05-17"})],
        signals=[SignalResult(code="161725", signal="hold", reason="Hold", name="Fund", type="fund")],
        portfolio_warnings=["demo warning"],
        rules={"source": "default", "config": {}},
        data_source="mock",
    )


class ReporterTests(unittest.TestCase):
    def test_offline_reporter_generates_markdown(self):
        output = OfflineReporter().render(_sample_result())
        self.assertIn("# Asset Analysis Report", output.report_md)
        self.assertEqual(output.used, "offline")

    def test_reporter_registry_returns_offline_by_default(self):
        reporter = get_reporter()
        self.assertEqual(reporter.name, "offline")

    def test_auto_reporter_falls_back_to_offline_when_llm_config_missing(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            output = get_reporter("auto").render(_sample_result())
            self.assertEqual(output.used, "offline")
            self.assertIn("offline fallback used", output.report_md)

    def test_llm_reporter_can_be_mocked_successfully(self):
        with mock.patch.dict(
            os.environ,
            {
                "ASSET_ANALYSIS_LLM_PROVIDER": "mock-provider",
                "ASSET_ANALYSIS_LLM_API_KEY": "secret",
                "ASSET_ANALYSIS_LLM_BASE_URL": "https://example.test/v1/chat/completions",
                "ASSET_ANALYSIS_LLM_MODEL": "mock-model",
            },
            clear=True,
        ):
            with mock.patch.object(LLMReporter, "_call_provider", return_value="# LLM Report\n\nTest") as mocked_call:
                output = LLMReporter().render(_sample_result())
                self.assertEqual(output.used, "llm")
                self.assertEqual(output.provider, "mock-provider")
                self.assertEqual(output.model, "mock-model")
                self.assertIn("# LLM Report", output.report_md)
                mocked_call.assert_called_once()

    def test_pipeline_accepts_reporter_offline(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            input_file = Path(temp_dir) / "holdings.yaml"
            output_dir = Path(temp_dir) / "reports"
            input_file.write_text(
                'funds:\n  - code: "161725"\n    name: "Example Fund"\n    type: "fund"\n    cost_nav: 1.0\n    amount: 100\n    target_position: 1.0\n',
                encoding="utf-8",
            )
            exit_code = pipeline_main(["--input", str(input_file), "--output", str(output_dir), "--data-source", "mock", "--reporter", "offline"])
            self.assertEqual(exit_code, 0)

    def test_pipeline_accepts_reporter_auto(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            input_file = Path(temp_dir) / "holdings.yaml"
            output_dir = Path(temp_dir) / "reports"
            input_file.write_text(
                'funds:\n  - code: "161725"\n    name: "Example Fund"\n    type: "fund"\n    cost_nav: 1.0\n    amount: 100\n    target_position: 1.0\n',
                encoding="utf-8",
            )
            with mock.patch.dict(os.environ, {}, clear=True):
                exit_code = pipeline_main(["--input", str(input_file), "--output", str(output_dir), "--data-source", "mock", "--reporter", "auto"])
            self.assertEqual(exit_code, 0)

    def test_report_json_includes_reporter_metadata(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            input_file = Path(temp_dir) / "holdings.yaml"
            output_dir = Path(temp_dir) / "reports"
            input_file.write_text(
                'funds:\n  - code: "161725"\n    name: "Example Fund"\n    type: "fund"\n    cost_nav: 1.0\n    amount: 100\n    target_position: 1.0\n',
                encoding="utf-8",
            )
            result = run_asset_pipeline(input_file, output_dir, data_source="mock", reporter_mode="offline")
            payload = json.loads((output_dir / "report.json").read_text(encoding="utf-8"))
            self.assertEqual(result.reporter["used"], "offline")
            self.assertIn("reporter", payload)
            self.assertEqual(payload["reporter"]["mode"], "offline")
