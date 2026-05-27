import unittest

from asset_analysis.localization.formatter import localize_warning_entry


class LocalizationWarningCopyTests(unittest.TestCase):
    def test_max_single_position_warning_uses_asset_name(self):
        warning = localize_warning_entry(
            "110022 exceeds max_single_position with current weight 84.01%.",
            asset_name_map={"110022": "易方达消费行业股票"},
        )
        self.assertEqual(warning["text"], "易方达消费行业股票 当前仓位 84.01%，超过单只资产上限。")

    def test_max_fund_position_warning_is_localized(self):
        warning = localize_warning_entry("Total fund position 100.00% exceeds max_fund_position 80.00%.")
        self.assertEqual(warning["text"], "基金总仓位 100.00%，超过组合上限 80.00%。")

    def test_group_warning_is_localized(self):
        warning = localize_warning_entry("Group sector_theme current position 35.00% exceeds max_position 30.00%.")
        self.assertEqual(warning["text"], "行业主题 当前仓位 35.00%，超过分组上限 30.00%。")

    def test_group_under_target_warning_is_localized(self):
        warning = localize_warning_entry(
            "Group sector_theme current position 6.28% is below target_position 20.00% by more than the configured threshold."
        )
        self.assertEqual(warning["text"], "行业主题 当前仓位 6.28%，低于分组目标 20.00%，已超过分组偏离阈值。")

    def test_tag_concentration_warning_is_localized(self):
        warning = localize_warning_entry("Tag 消费 concentration 45.00% exceeds configured threshold 30.00%.")
        self.assertEqual(warning["text"], "消费 标签集中度 45.00%，超过阈值 30.00%。")

    def test_unknown_reason_falls_back_safely(self):
        warning = localize_warning_entry("unexpected english warning")
        self.assertTrue(warning["text"].startswith("规则提醒："))
