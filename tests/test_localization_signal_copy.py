import unittest

from asset_analysis.localization.formatter import localize_signal_entry, localize_signal_label
from asset_analysis.localization.group_copy import localize_group_name


class LocalizationSignalCopyTests(unittest.TestCase):
    def test_signal_labels_are_localized(self):
        self.assertEqual(localize_signal_label("add"), "可补仓观察")
        self.assertEqual(localize_signal_label("reduce"), "建议减仓观察")
        self.assertEqual(localize_signal_label("hold"), "继续持有观察")

    def test_group_names_are_localized(self):
        self.assertEqual(localize_group_name("sector_theme"), "行业主题")
        self.assertEqual(localize_group_name("money_market"), "货币/现金类")
        self.assertEqual(localize_group_name("other"), "其他")

    def test_below_target_reason_is_localized(self):
        signal = localize_signal_entry(
            {
                "code": "161725",
                "name": "招商中证白酒指数(LOF)A",
                "signal": "add",
                "reason": "Current position 6.28% is below target 20.00% by more than the rebalance band.",
            }
        )
        self.assertEqual(signal["signal_label"], "可补仓观察")
        self.assertIn("低于目标仓位 20.00%", signal["reason_cn"])

    def test_above_target_reason_is_localized(self):
        signal = localize_signal_entry(
            {
                "code": "110022",
                "name": "易方达消费行业股票",
                "signal": "reduce",
                "reason": "Current position 84.01% is above target 30.00% by more than the overweight band.",
            }
        )
        self.assertEqual(signal["signal_label"], "建议减仓观察")
        self.assertIn("高于目标仓位 30.00%", signal["reason_cn"])
