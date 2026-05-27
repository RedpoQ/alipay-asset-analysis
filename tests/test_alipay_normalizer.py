import unittest

from asset_analysis.alipay_parser import convert_records_to_holdings


class AlipayNormalizerTests(unittest.TestCase):
    def test_fund_code_preserves_leading_zeros(self):
        result = convert_records_to_holdings(
            [{"基金代码": "000001", "基金名称": "华夏成长混合", "持有金额": "500", "持仓成本价": "1.20"}]
        )
        self.assertEqual(result.holdings["funds"][0]["code"], "000001")

    def test_comma_and_rmb_amounts_are_parsed(self):
        result = convert_records_to_holdings(
            [{"基金代码": "000001", "基金名称": "华夏成长混合", "持有金额": "￥1，234.56", "持仓成本价": "1.20"}]
        )
        self.assertAlmostEqual(result.holdings["funds"][0]["amount"], 1234.56)

    def test_percent_fields_are_parsed_as_decimals(self):
        result = convert_records_to_holdings(
            [{"基金代码": "000001", "基金名称": "华夏成长混合", "持有金额": "500", "持仓成本价": "1.20", "收益率": "-2.94%", "目标仓位": "25%"}]
        )
        row = result.normalized_rows[0]
        self.assertAlmostEqual(row["profit_rate"], -0.0294)
        self.assertAlmostEqual(row["target_position"], 0.25)

    def test_missing_optional_values_create_warnings(self):
        result = convert_records_to_holdings(
            [{"基金代码": "000001", "基金名称": "华夏成长混合", "持有金额": "500", "持仓成本价": "1.20", "收益率": "--"}]
        )
        self.assertTrue(any("profit_rate" in item.message for item in result.warnings))

    def test_missing_required_values_create_row_errors(self):
        result = convert_records_to_holdings(
            [{"基金代码": "", "基金名称": "华夏成长混合", "持有金额": "500", "持仓成本价": "1.20"}]
        )
        self.assertEqual(result.valid_count, 0)
        self.assertTrue(result.errors)


if __name__ == "__main__":
    unittest.main()
