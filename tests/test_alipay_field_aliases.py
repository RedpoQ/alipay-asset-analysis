import unittest

from asset_analysis.alipay.field_aliases import normalize_header_name, resolve_canonical_field


class AlipayFieldAliasesTests(unittest.TestCase):
    def test_chinese_aliases_map_to_canonical_fields(self):
        self.assertEqual(resolve_canonical_field("基金代码"), "code")
        self.assertEqual(resolve_canonical_field("产品名称"), "name")
        self.assertEqual(resolve_canonical_field("持有市值"), "market_value")
        self.assertEqual(resolve_canonical_field("持仓成本"), "cost_nav")
        self.assertEqual(resolve_canonical_field("目标占比"), "target_position")

    def test_english_aliases_map_to_canonical_fields_case_insensitively(self):
        self.assertEqual(resolve_canonical_field("FUND_CODE"), "code")
        self.assertEqual(resolve_canonical_field("Fund_Name"), "name")
        self.assertEqual(resolve_canonical_field("LATEST_NAV"), "current_nav")
        self.assertEqual(resolve_canonical_field("target_weight"), "target_position")

    def test_headers_with_parentheses_normalize(self):
        self.assertEqual(resolve_canonical_field("持有金额(元)"), "market_value")
        self.assertEqual(resolve_canonical_field("持有金额（元）"), "market_value")

    def test_bom_and_whitespace_are_ignored(self):
        self.assertEqual(resolve_canonical_field("\ufeff 基金代码 "), "code")
        self.assertEqual(normalize_header_name("  收益率　"), "收益率")


if __name__ == "__main__":
    unittest.main()
