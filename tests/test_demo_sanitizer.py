import unittest

from asset_analysis.demo.sanitizer import sanitize_report


def _sample_report() -> dict:
    return {
        "schema_version": "1.0.0",
        "run": {
            "input": r"C:\Users\demo\private\holdings.local.yaml",
            "output_dir": "reports/private/latest",
        },
        "summary": {
            "total_cost": 5392.0,
            "total_market_value": 6427.27,
            "total_profit": 239.59,
            "total_profit_rate": 0.0387,
        },
        "positions": [
            {
                "code": "000001",
                "name": "华夏成长混合",
                "type": "fund",
                "cost": 480.0,
                "market_value": 500.0,
                "profit": 20.0,
                "profit_rate": 0.0417,
                "target_position": 0.25,
                "current_position": 0.1,
                "metadata": {"notes": "private note"},
                "quote": {
                    "name": "华夏成长混合",
                    "current_nav": 1.25,
                    "current_price": 1.25,
                    "previous_nav": 1.20,
                    "daily_change_rate": 0.0417,
                    "raw": {"path": r"C:\Users\demo\private\raw.json"},
                },
            }
        ],
        "signals": [
            {
                "code": "000001",
                "name": "华夏成长混合",
                "signal": "add",
                "reason": "Current position 10.00% is below target 25.00%.",
            }
        ],
        "portfolio_warnings": ["华夏成长混合 current weight 10.00% is below target."],
        "report_md": "Path: C:/Users/demo/private/config.local.yaml",
    }


class DemoSanitizerTests(unittest.TestCase):
    def test_sanitizer_masks_private_windows_paths(self):
        payload = sanitize_report(_sample_report(), mode="public")
        self.assertNotIn("C:\\Users\\", str(payload))

    def test_sanitizer_removes_private_paths(self):
        payload = sanitize_report(_sample_report(), mode="public")
        self.assertNotIn("private/", str(payload))
        self.assertNotIn("private\\", str(payload))

    def test_sanitizer_normalizes_amounts(self):
        payload = sanitize_report(_sample_report(), mode="public")
        self.assertEqual(payload["summary"]["total_market_value"], 10000.0)
        self.assertNotEqual(payload["positions"][0]["market_value"], 500.0)

    def test_sanitizer_preserves_signal_values(self):
        payload = sanitize_report(_sample_report(), mode="public")
        self.assertEqual(payload["signals"][0]["signal"], "add")

    def test_sanitizer_preserves_percentages(self):
        payload = sanitize_report(_sample_report(), mode="public")
        self.assertAlmostEqual(payload["summary"]["total_profit_rate"], 0.0387)
        self.assertAlmostEqual(payload["positions"][0]["profit_rate"], 0.0417)
        self.assertAlmostEqual(payload["positions"][0]["current_position"], 0.1)
        self.assertAlmostEqual(payload["positions"][0]["target_position"], 0.25)

    def test_minimal_mode_removes_position_detail(self):
        payload = sanitize_report(_sample_report(), mode="minimal")
        self.assertEqual(payload["positions"], [])


if __name__ == "__main__":
    unittest.main()
