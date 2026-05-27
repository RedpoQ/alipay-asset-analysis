import json
import tempfile
import unittest
from pathlib import Path

from asset_analysis.history.compare import compare_reports


class SnapshotCompareTests(unittest.TestCase):
    def test_compare_reports_detects_signal_changes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            current, previous = _write_pair(Path(temp_dir), current_signal="reduce", previous_signal="hold")
            result = compare_reports(str(current), str(previous))
            self.assertEqual(result["signal_changes"][0]["current_signal"], "reduce")

    def test_compare_reports_detects_summary_deltas(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            current, previous = _write_pair(Path(temp_dir), current_profit=20, previous_profit=10)
            result = compare_reports(str(current), str(previous))
            self.assertEqual(result["summary_delta"]["total_profit_delta"], 10.0)

    def test_compare_reports_detects_new_and_resolved_warnings(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            current, previous = _write_pair(
                Path(temp_dir),
                current_warnings=["new_warning"],
                previous_warnings=["old_warning"],
            )
            result = compare_reports(str(current), str(previous))
            self.assertIn("new_warning", result["warning_changes"]["new"])
            self.assertIn("old_warning", result["warning_changes"]["resolved"])

    def test_group_changes_are_handled_when_group_analysis_exists(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            current, previous = _write_pair(Path(temp_dir), current_group_position=0.4, previous_group_position=0.2)
            result = compare_reports(str(current), str(previous))
            self.assertEqual(result["group_changes"][0]["group_position_delta"], 0.2)


def _write_pair(
    base: Path,
    current_signal: str = "hold",
    previous_signal: str = "hold",
    current_profit: float = 10,
    previous_profit: float = 10,
    current_warnings: list[str] | None = None,
    previous_warnings: list[str] | None = None,
    current_group_position: float = 0.2,
    previous_group_position: float = 0.2,
) -> tuple[Path, Path]:
    current = base / "current.json"
    previous = base / "previous.json"
    current.write_text(
        json.dumps(
            {
                "summary": {"total_market_value": 120, "total_profit": current_profit, "total_profit_rate": 0.2},
                "signals": [{"code": "A", "name": "Asset", "signal": current_signal}],
                "positions": [{"code": "A", "name": "Asset", "current_position": 0.3, "profit_rate": 0.2}],
                "portfolio_warnings": current_warnings or [],
                "group_analysis": {"groups": [{"group": "active_equity", "current_position": current_group_position, "warnings": []}]},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    previous.write_text(
        json.dumps(
            {
                "summary": {"total_market_value": 100, "total_profit": previous_profit, "total_profit_rate": 0.1},
                "signals": [{"code": "A", "name": "Asset", "signal": previous_signal}],
                "positions": [{"code": "A", "name": "Asset", "current_position": 0.1, "profit_rate": 0.1}],
                "portfolio_warnings": previous_warnings or [],
                "group_analysis": {"groups": [{"group": "active_equity", "current_position": previous_group_position, "warnings": []}]},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return current, previous
