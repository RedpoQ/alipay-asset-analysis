import json
import tempfile
import unittest
from pathlib import Path

from asset_analysis.alipay_parser import (
    convert_records_to_holdings,
    main,
    parse_alipay_file,
    write_converted_holdings,
)
from asset_analysis.pipeline import run_asset_pipeline


class AlipayParserTests(unittest.TestCase):
    def test_parse_chinese_csv_headers(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            input_file = Path(temp_dir) / "alipay.csv"
            input_file.write_text(
                "基金代码,基金名称,持有金额,持有份额,持仓成本价,最新净值,收益率,目标仓位\n"
                "161725,招商中证白酒指数A,1200,980,0.923,0.951,3.04,0.35\n",
                encoding="utf-8",
            )
            result = parse_alipay_file(input_file)
            self.assertEqual(result.valid_count, 1)
            self.assertEqual(result.holdings["funds"][0]["code"], "161725")

    def test_parse_english_csv_headers(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            input_file = Path(temp_dir) / "alipay.csv"
            input_file.write_text(
                "code,name,market_value,shares,cost_nav,current_nav,profit_rate,target_position\n"
                "000001,Example Fund,500,300,1.234,1.300,5.35,0.25\n",
                encoding="utf-8",
            )
            result = parse_alipay_file(input_file)
            self.assertEqual(result.valid_count, 1)
            self.assertAlmostEqual(result.holdings["funds"][0]["cost_nav"], 1.234)

    def test_parse_json_input(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            input_file = Path(temp_dir) / "alipay.json"
            input_file.write_text(
                json.dumps(
                    [
                        {
                            "code": "000001",
                            "name": "Example Fund",
                            "market_value": 500,
                            "shares": 300,
                            "cost_nav": 1.234,
                            "target_position": 0.25,
                        }
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            result = parse_alipay_file(input_file)
            self.assertEqual(result.valid_count, 1)
            self.assertEqual(result.holdings["funds"][0]["type"], "fund")

    def test_generate_standard_holdings_dict(self):
        result = convert_records_to_holdings(
            [
                {
                    "code": "000001",
                    "name": "Example Fund",
                    "market_value": 500,
                    "shares": 300,
                    "cost_nav": 1.234,
                    "target_position": 0.25,
                }
            ]
        )
        self.assertIn("funds", result.holdings)
        self.assertEqual(result.holdings["funds"][0]["amount"], 500.0)

    def test_write_yaml_output(self):
        result = convert_records_to_holdings(
            [{"code": "000001", "name": "Example Fund", "market_value": 500, "shares": 300, "cost_nav": 1.234}]
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = Path(temp_dir) / "converted" / "holdings.yaml"
            write_converted_holdings(result, output_file, output_format="yaml")
            self.assertTrue(output_file.exists())
            content = output_file.read_text(encoding="utf-8")
            self.assertIn("funds:", content)
            self.assertIn('code: "000001"', content)

    def test_write_json_output(self):
        result = convert_records_to_holdings(
            [{"code": "000001", "name": "Example Fund", "market_value": 500, "shares": 300, "cost_nav": 1.234}]
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = Path(temp_dir) / "converted" / "holdings.json"
            write_converted_holdings(result, output_file, output_format="json")
            self.assertTrue(output_file.exists())
            payload = json.loads(output_file.read_text(encoding="utf-8"))
            self.assertIn("funds", payload)

    def test_invalid_row_produces_warning_or_error(self):
        result = convert_records_to_holdings(
            [
                {"code": "000001", "name": "Example Fund", "market_value": 500, "shares": 300, "cost_nav": 1.234},
                {"code": "", "name": "Broken Fund", "market_value": 500},
            ]
        )
        self.assertEqual(result.valid_count, 1)
        self.assertTrue(result.errors)

    def test_converted_holdings_can_be_consumed_by_pipeline(self):
        result = convert_records_to_holdings(
            [
                {
                    "基金代码": "161725",
                    "基金名称": "招商中证白酒指数A",
                    "持有金额": 1200,
                    "持有份额": 980,
                    "持仓成本价": 0.923,
                    "目标仓位": 0.35,
                }
            ]
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            holdings_path = Path(temp_dir) / "converted.yaml"
            output_dir = Path(temp_dir) / "reports"
            write_converted_holdings(result, holdings_path)
            pipeline_result = run_asset_pipeline(holdings_path, output_dir, data_source="mock")
            self.assertTrue((output_dir / "report.json").exists())
            self.assertGreater(pipeline_result.summary.total_cost, 0)

    def test_main_returns_non_zero_for_fully_invalid_data(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            input_file = Path(temp_dir) / "broken.csv"
            input_file.write_text("基金代码,基金名称,持有金额\n,,0\n", encoding="utf-8")
            output_file = Path(temp_dir) / "converted.yaml"
            exit_code = main(["--input", str(input_file), "--output", str(output_file)])
            self.assertEqual(exit_code, 1)
