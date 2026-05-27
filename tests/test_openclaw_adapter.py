import json
import tempfile
import unittest
from pathlib import Path

from asset_analysis.openclaw_adapter import main as adapter_main, run_asset_analysis_skill
from openclaw_skill.asset_analysis_skill import run as run_openclaw_skill


class OpenClawAdapterTests(unittest.TestCase):
    def test_adapter_runs_with_standard_holdings_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            holdings = base / "holdings.yaml"
            output_dir = base / "reports"
            holdings.write_text(
                'funds:\n  - code: "161725"\n    name: "Example Fund"\n    type: "fund"\n    cost_nav: 1.0\n    amount: 100\n    target_position: 1.0\n',
                encoding="utf-8",
            )
            result = run_asset_analysis_skill(str(holdings), str(output_dir))
            self.assertTrue(result["ok"])

    def test_adapter_returns_ok_true_and_report_paths(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            holdings = base / "holdings.yaml"
            output_dir = base / "reports"
            holdings.write_text(
                'funds:\n  - code: "161725"\n    name: "Example Fund"\n    type: "fund"\n    cost_nav: 1.0\n    amount: 100\n    target_position: 1.0\n',
                encoding="utf-8",
            )
            result = run_asset_analysis_skill(str(holdings), str(output_dir))
            self.assertTrue(Path(result["report_json"]).exists())
            self.assertTrue(Path(result["report_md"]).exists())

    def test_adapter_output_contains_summary_signals_portfolio_warnings(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            holdings = base / "holdings.yaml"
            output_dir = base / "reports"
            holdings.write_text(
                'funds:\n  - code: "161725"\n    name: "Example Fund"\n    type: "fund"\n    cost_nav: 1.0\n    amount: 100\n    target_position: 1.0\n',
                encoding="utf-8",
            )
            result = run_asset_analysis_skill(str(holdings), str(output_dir))
            self.assertIsInstance(result["summary"], dict)
            self.assertIsInstance(result["signals"], list)
            self.assertIsInstance(result["portfolio_warnings"], list)

    def test_adapter_can_convert_alipay_csv_then_run_pipeline(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            csv_path = base / "alipay.csv"
            output_dir = base / "reports"
            csv_path.write_text(
                "基金代码,基金名称,持有金额,持有份额,持仓成本价,目标仓位\n161725,招商中证白酒指数A,1200,980,0.923,0.35\n",
                encoding="utf-8",
            )
            result = run_asset_analysis_skill(
                holdings_path="",
                output_dir=str(output_dir),
                alipay_input_path=str(csv_path),
            )
            self.assertTrue(result["ok"])
            self.assertTrue(Path(result["converted_holdings"]).exists())

    def test_invalid_holdings_path_returns_ok_false(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            result = run_asset_analysis_skill("missing.yaml", str(Path(temp_dir) / "reports"))
            self.assertFalse(result["ok"])
            self.assertTrue(result["errors"])

    def test_invalid_rules_path_returns_ok_false(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            holdings = base / "holdings.yaml"
            output_dir = base / "reports"
            holdings.write_text(
                'funds:\n  - code: "161725"\n    name: "Example Fund"\n    type: "fund"\n    cost_nav: 1.0\n    amount: 100\n    target_position: 1.0\n',
                encoding="utf-8",
            )
            result = run_asset_analysis_skill(str(holdings), str(output_dir), rules_path=str(base / "missing_rules.yaml"))
            self.assertFalse(result["ok"])

    def test_openclaw_skill_wrapper_returns_json_serializable_dict(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            holdings = base / "holdings.yaml"
            output_dir = base / "reports"
            holdings.write_text(
                'funds:\n  - code: "161725"\n    name: "Example Fund"\n    type: "fund"\n    cost_nav: 1.0\n    amount: 100\n    target_position: 1.0\n',
                encoding="utf-8",
            )
            result = run_openclaw_skill({"holdings_path": str(holdings), "output_dir": str(output_dir)})
            json.dumps(result, ensure_ascii=False)
            self.assertIn("ok", result)

    def test_adapter_cli_returns_zero_on_success(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            holdings = base / "holdings.yaml"
            output_dir = base / "reports"
            holdings.write_text(
                'funds:\n  - code: "161725"\n    name: "Example Fund"\n    type: "fund"\n    cost_nav: 1.0\n    amount: 100\n    target_position: 1.0\n',
                encoding="utf-8",
            )
            exit_code = adapter_main(["--holdings", str(holdings), "--output", str(output_dir), "--data-source", "mock", "--reporter", "offline"])
            self.assertEqual(exit_code, 0)
