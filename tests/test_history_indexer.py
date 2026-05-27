import json
import tempfile
import unittest
from pathlib import Path

from asset_analysis.history.indexer import build_history_index


class HistoryIndexerTests(unittest.TestCase):
    def test_indexer_handles_empty_reports_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            reports_dir = Path(temp_dir) / "daily"
            output = Path(temp_dir) / "history_index.json"
            result = build_history_index(str(reports_dir), str(output))
            self.assertEqual(result["count"], 0)
            self.assertTrue(output.exists())

    def test_indexer_indexes_valid_reports(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            dated = base / "daily" / "2026-05-18"
            dated.mkdir(parents=True)
            report = {
                "generated_at": "2026-05-18T12:00:00+08:00",
                "summary": {"total_cost": 100, "total_market_value": 110, "total_profit": 10, "total_profit_rate": 0.1},
                "signals": [{"signal": "add"}, {"signal": "hold"}],
                "portfolio_warnings": ["w1"],
                "group_analysis": {"warnings": ["gw1"]},
            }
            (dated / "report.json").write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")
            result = build_history_index(str(base / "daily"), str(base / "history_index.json"))
            self.assertEqual(result["count"], 1)
            self.assertEqual(result["items"][0]["signals_summary"]["add"], 1)

    def test_invalid_report_is_skipped_with_warning(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            dated = base / "daily" / "2026-05-18"
            dated.mkdir(parents=True)
            (dated / "report.json").write_text("not-json", encoding="utf-8")
            result = build_history_index(str(base / "daily"), str(base / "history_index.json"))
            self.assertEqual(result["count"], 0)
            self.assertTrue(result["warnings"])
