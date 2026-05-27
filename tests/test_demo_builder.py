import json
import tempfile
import unittest
from pathlib import Path

from asset_analysis.demo.demo_builder import build_builtin_demo_payload, build_sanitized_report_payload


class DemoBuilderTests(unittest.TestCase):
    def test_build_sanitized_report_payload_from_source(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            report_path = Path(temp_dir) / "report.json"
            report_path.write_text(
                json.dumps(
                    {
                        "schema_version": "1.0.0",
                        "summary": {
                            "total_cost": 100.0,
                            "total_market_value": 120.0,
                            "total_profit": 20.0,
                            "total_profit_rate": 0.2,
                        },
                        "positions": [],
                        "signals": [],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            payload = build_sanitized_report_payload(str(report_path), mode="public")
            self.assertEqual(payload["summary"]["total_market_value"], 10000.0)

    def test_build_builtin_demo_payload_returns_report_and_preflight(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            payload, preflight = build_builtin_demo_payload(temp_dir, mode="realistic_demo")
            self.assertEqual(payload["schema_version"], "1.0.0")
            self.assertIsInstance(preflight, dict)
            self.assertTrue(preflight["ok"])


if __name__ == "__main__":
    unittest.main()
