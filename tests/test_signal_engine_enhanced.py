import json
import tempfile
import unittest
from pathlib import Path

from asset_analysis.models import AssetPosition
from asset_analysis.rules.config import RuleConfig
from asset_analysis.signal_engine import SignalEngine
from asset_analysis.pipeline import main as pipeline_main, run_asset_pipeline


class EnhancedSignalEngineTests(unittest.TestCase):
    def test_underweight_asset_gets_add(self):
        engine = SignalEngine(RuleConfig())
        position = AssetPosition(code="F1", name="Fund1", type="fund", cost=1000, market_value=700, profit=-50, profit_rate=-0.05, target_position=0.4, current_position=0.2)
        self.assertEqual(engine.evaluate(position).signal, "add")

    def test_overweight_asset_gets_reduce(self):
        engine = SignalEngine(RuleConfig())
        position = AssetPosition(code="F1", name="Fund1", type="fund", cost=1000, market_value=1400, profit=400, profit_rate=0.4, target_position=0.2, current_position=0.4)
        self.assertEqual(engine.evaluate(position).signal, "reduce")

    def test_near_target_asset_gets_hold(self):
        engine = SignalEngine(RuleConfig())
        position = AssetPosition(code="F1", name="Fund1", type="fund", cost=1000, market_value=1010, profit=10, profit_rate=0.01, target_position=0.25, current_position=0.22)
        self.assertEqual(engine.evaluate(position).signal, "hold")

    def test_deep_loss_blocks_add(self):
        engine = SignalEngine(RuleConfig())
        position = AssetPosition(code="F1", name="Fund1", type="fund", cost=1000, market_value=700, profit=-300, profit_rate=-0.3, target_position=0.5, current_position=0.2)
        result = engine.evaluate(position)
        self.assertEqual(result.signal, "hold")
        self.assertTrue(result.blocked_by)

    def test_failed_quote_leads_to_conservative_hold_warning(self):
        engine = SignalEngine(RuleConfig())
        position = AssetPosition(code="F1", name="Fund1", type="fund", cost=1000, market_value=0, profit=-1000, profit_rate=-1.0, target_position=0.5, current_position=0.0, error={"code": "FETCH_ERROR", "message": "boom"})
        result = engine.evaluate(position)
        self.assertEqual(result.signal, "hold")
        self.assertTrue(result.warnings)

    def test_max_single_position_creates_warning(self):
        engine = SignalEngine(RuleConfig())
        position = AssetPosition(code="F1", name="Fund1", type="fund", cost=1000, market_value=1500, profit=500, profit_rate=0.5, target_position=0.2, current_position=0.5)
        result = engine.evaluate(position)
        self.assertTrue(result.warnings)

    def test_pipeline_accepts_rules(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            input_file = Path(temp_dir) / "holdings.yaml"
            rules_file = Path(temp_dir) / "rules.yaml"
            output_dir = Path(temp_dir) / "reports"
            input_file.write_text(
                'funds:\n  - code: "161725"\n    name: "Example Fund"\n    type: "fund"\n    cost_nav: 1.0\n    amount: 100\n    target_position: 1.0\n',
                encoding="utf-8",
            )
            rules_file.write_text("portfolio:\n  max_single_position: 0.25\n", encoding="utf-8")
            exit_code = pipeline_main(["--input", str(input_file), "--output", str(output_dir), "--data-source", "mock", "--rules", str(rules_file)])
            self.assertEqual(exit_code, 0)

    def test_pipeline_returns_non_zero_for_invalid_rules(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            input_file = Path(temp_dir) / "holdings.yaml"
            rules_file = Path(temp_dir) / "rules.yaml"
            output_dir = Path(temp_dir) / "reports"
            input_file.write_text(
                'funds:\n  - code: "161725"\n    name: "Example Fund"\n    type: "fund"\n    cost_nav: 1.0\n    amount: 100\n    target_position: 1.0\n',
                encoding="utf-8",
            )
            rules_file.write_text("portfolio:\n  max_single_position:\n    - invalid\n", encoding="utf-8")
            exit_code = pipeline_main(["--input", str(input_file), "--output", str(output_dir), "--data-source", "mock", "--rules", str(rules_file)])
            self.assertEqual(exit_code, 1)

    def test_report_json_includes_structured_signals_and_portfolio_warnings(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            input_file = Path(temp_dir) / "holdings.yaml"
            output_dir = Path(temp_dir) / "reports"
            input_file.write_text(
                'funds:\n  - code: "161725"\n    name: "Example Fund"\n    type: "fund"\n    cost_nav: 1.0\n    amount: 100\n    target_position: 1.0\n',
                encoding="utf-8",
            )
            run_asset_pipeline(input_file, output_dir, data_source="mock")
            payload = json.loads((output_dir / "report.json").read_text(encoding="utf-8"))
            self.assertIn("portfolio_warnings", payload)
            self.assertIn("confidence", payload["signals"][0])
            self.assertIn("severity", payload["signals"][0])
