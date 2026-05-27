import json
import tempfile
import unittest
from pathlib import Path

from asset_analysis.history.indexer import build_history_index
from asset_analysis.history.trend_reporter import build_trend_report
from asset_analysis.workflow.daily_run import run_daily_workflow


class TrendReporterTests(unittest.TestCase):
    def test_trend_reporter_generates_markdown(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            _write_history_report(base / "daily" / "2026-05-17", "2026-05-17T12:00:00+08:00", 0.1)
            _write_history_report(base / "daily" / "2026-05-18", "2026-05-18T12:00:00+08:00", 0.2)
            build_history_index(str(base / "daily"), str(base / "history_index.json"))
            payload = build_trend_report(index_path=str(base / "history_index.json"), output_path=str(base / "trend" / "latest_trend.md"))
            self.assertIn("历史报告概览", payload["report_md"])
            self.assertTrue((base / "trend" / "latest_trend.md").exists())

    def test_daily_workflow_can_update_history_index(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            private_dir = base / "private"
            private_dir.mkdir()
            holdings_path = private_dir / "holdings.local.yaml"
            holdings_path.write_text(
                'funds:\n  - code: "161725"\n    name: "Fund"\n    type: "fund"\n    cost_nav: 1.0\n    amount: 100\n    target_position: 1.0\n',
                encoding="utf-8",
            )
            config = base / "config.local.yaml"
            config.write_text(
                "\n".join(
                    [
                        "input:",
                        "  mode: holdings_yaml",
                        f"  holdings_yaml: {holdings_path.as_posix()}",
                        "output:",
                        f"  daily_dir: {(base / 'reports' / 'daily').as_posix()}",
                        f"  latest_dir: {(base / 'reports' / 'private' / 'latest').as_posix()}",
                        "analysis:",
                        "  data_source: mock",
                        "  reporter: offline",
                        "notification:",
                        "  enabled: false",
                        "history:",
                        "  enabled: true",
                        f"  reports_dir: {(base / 'reports' / 'daily').as_posix()}",
                        f"  index_path: {(base / 'reports' / 'history_index.json').as_posix()}",
                        f"  trend_output_dir: {(base / 'reports' / 'trend').as_posix()}",
                    ]
                ),
                encoding="utf-8",
            )
            result = run_daily_workflow(str(config))
            self.assertTrue(result["ok"])
            self.assertTrue((base / "reports" / "history_index.json").exists())

    def test_history_failure_does_not_break_successful_daily_report_generation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            private_dir = base / "private"
            private_dir.mkdir()
            holdings_path = private_dir / "holdings.local.yaml"
            holdings_path.write_text(
                'funds:\n  - code: "161725"\n    name: "Fund"\n    type: "fund"\n    cost_nav: 1.0\n    amount: 100\n    target_position: 1.0\n',
                encoding="utf-8",
            )
            config = base / "config.local.yaml"
            occupied = base / "occupied"
            occupied.write_text("x", encoding="utf-8")
            config.write_text(
                "\n".join(
                    [
                        "input:",
                        "  mode: holdings_yaml",
                        f"  holdings_yaml: {holdings_path.as_posix()}",
                        "output:",
                        f"  daily_dir: {(base / 'reports' / 'daily').as_posix()}",
                        f"  latest_dir: {(base / 'reports' / 'private' / 'latest').as_posix()}",
                        "analysis:",
                        "  data_source: mock",
                        "  reporter: offline",
                        "notification:",
                        "  enabled: false",
                        "history:",
                        "  enabled: true",
                        f"  reports_dir: {(base / 'reports' / 'daily').as_posix()}",
                        f"  index_path: {(occupied / 'history_index.json').as_posix()}",
                        f"  trend_output_dir: {(base / 'reports' / 'trend').as_posix()}",
                    ]
                ),
                encoding="utf-8",
            )
            result = run_daily_workflow(str(config))
            self.assertTrue(result["ok"])
            self.assertTrue(any("History generation failed" in item for item in result["warnings"]))


def _write_history_report(target_dir: Path, generated_at: str, profit_rate: float) -> None:
    target_dir.mkdir(parents=True)
    (target_dir / "report.json").write_text(
        json.dumps(
            {
                "generated_at": generated_at,
                "summary": {
                    "total_cost": 100,
                    "total_market_value": 100 + profit_rate * 100,
                    "total_profit": profit_rate * 100,
                    "total_profit_rate": profit_rate,
                },
                "signals": [{"code": "A", "name": "Asset", "signal": "hold"}],
                "positions": [{"code": "A", "name": "Asset", "current_position": 1.0, "profit_rate": profit_rate}],
                "portfolio_warnings": [],
                "group_analysis": {"groups": [{"group": "other", "current_position": 1.0, "warnings": []}], "warnings": []},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
