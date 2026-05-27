import tempfile
import unittest
from pathlib import Path

from asset_analysis.alipay.preview import build_preview_payload


class AlipayPreviewTests(unittest.TestCase):
    def test_preview_detects_mapping_and_row_counts(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "alipay.csv"
            csv_path.write_text(
                "\ufeff基金代码,基金名称,持有金额（元）,持仓成本价,收益率,目标仓位\n000001,华夏成长混合,1，234.56,1.20,5.35%,25%\n",
                encoding="utf-8",
            )
            payload = build_preview_payload(csv_path)
            self.assertEqual(payload["canonical_field_mapping"]["code"], "基金代码")
            self.assertEqual(payload["canonical_field_mapping"]["market_value"], "持有金额（元）")
            self.assertEqual(payload["valid_rows_count"], 1)
            self.assertEqual(payload["invalid_rows_count"], 0)
            self.assertEqual(payload["first_normalized_rows"][0]["code"], "000001")


if __name__ == "__main__":
    unittest.main()
