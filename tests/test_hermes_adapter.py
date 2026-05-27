import json
import tempfile
import unittest
from pathlib import Path

from asset_analysis.hermes_adapter import main as hermes_main, run_daily_asset_analysis_task


class HermesAdapterTests(unittest.TestCase):
    def test_hermes_adapter_runs_with_holdings_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            holdings = base / "holdings.yaml"
            output_dir = base / "reports"
            holdings.write_text(
                'funds:\n  - code: "161725"\n    name: "Example Fund"\n    type: "fund"\n    cost_nav: 1.0\n    amount: 100\n    target_position: 1.0\n',
                encoding="utf-8",
            )
            result = run_daily_asset_analysis_task(holdings_path=str(holdings), output_dir=str(output_dir))
            self.assertTrue(result["ok"])

    def test_hermes_adapter_runs_with_alipay_input_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            csv_path = base / "alipay.csv"
            output_dir = base / "reports"
            csv_path.write_text(
                "基金代码,基金名称,持有金额,持有份额,持仓成本价,目标仓位\n161725,招商中证白酒指数A,1200,980,0.923,0.35\n",
                encoding="utf-8",
            )
            result = run_daily_asset_analysis_task(alipay_input_path=str(csv_path), output_dir=str(output_dir))
            self.assertTrue(result["ok"])

    def test_missing_input_returns_ok_false(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            result = run_daily_asset_analysis_task(output_dir=str(Path(temp_dir) / "reports"))
            self.assertFalse(result["ok"])

    def test_invalid_holdings_path_returns_ok_false(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            result = run_daily_asset_analysis_task(holdings_path="missing.yaml", output_dir=str(Path(temp_dir) / "reports"))
            self.assertFalse(result["ok"])

    def test_returned_result_is_json_serializable(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            holdings = base / "holdings.yaml"
            output_dir = base / "reports"
            holdings.write_text(
                'funds:\n  - code: "161725"\n    name: "Example Fund"\n    type: "fund"\n    cost_nav: 1.0\n    amount: 100\n    target_position: 1.0\n',
                encoding="utf-8",
            )
            result = run_daily_asset_analysis_task(holdings_path=str(holdings), output_dir=str(output_dir))
            json.dumps(result, ensure_ascii=False)
            self.assertIn("task", result)

    def test_signals_summary_counts_add_reduce_hold_correctly(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            holdings = base / "holdings.yaml"
            output_dir = base / "reports"
            holdings.write_text(
                'funds:\n  - code: "161725"\n    name: "Example Fund"\n    type: "fund"\n    cost_nav: 1.0\n    amount: 100\n    target_position: 1.0\n',
                encoding="utf-8",
            )
            result = run_daily_asset_analysis_task(holdings_path=str(holdings), output_dir=str(output_dir))
            total = sum(result["signals_summary"].values())
            self.assertEqual(total, len(result["top_signals"]))

    def test_daily_message_contains_rule_based_limitation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            holdings = base / "holdings.yaml"
            output_dir = base / "reports"
            holdings.write_text(
                'funds:\n  - code: "161725"\n    name: "Example Fund"\n    type: "fund"\n    cost_nav: 1.0\n    amount: 100\n    target_position: 1.0\n',
                encoding="utf-8",
            )
            result = run_daily_asset_analysis_task(holdings_path=str(holdings), output_dir=str(output_dir))
            self.assertIn("规则驱动", result["daily_message"])

    def test_cli_style_function_path_does_not_require_network(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            holdings = base / "holdings.yaml"
            output_dir = base / "reports"
            holdings.write_text(
                'funds:\n  - code: "161725"\n    name: "Example Fund"\n    type: "fund"\n    cost_nav: 1.0\n    amount: 100\n    target_position: 1.0\n',
                encoding="utf-8",
            )
            exit_code = hermes_main(["--holdings", str(holdings), "--output", str(output_dir), "--data-source", "mock", "--reporter", "offline"])
            self.assertEqual(exit_code, 0)
