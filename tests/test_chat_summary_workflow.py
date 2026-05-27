import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from asset_analysis.chat_summary.cli import main as chat_summary_main
from asset_analysis.notifications.message_builder import build_notification_message
from asset_analysis.workflow.daily_run import run_daily_workflow
from asset_analysis.hermes_adapter import run_daily_asset_analysis_task
from asset_analysis.release.checks import run_chat_summary_smoke_check


class ChatSummaryWorkflowTests(unittest.TestCase):
    def test_cli_writes_chat_summary_txt_and_json(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            report = _write_report(base)
            txt_path = base / "chat_summary.txt"
            json_path = base / "chat_summary.json"
            code = chat_summary_main(["--report", str(report), "--output", str(txt_path), "--json-output", str(json_path)])
            self.assertEqual(code, 0)
            self.assertTrue(txt_path.exists())
            self.assertTrue(json_path.exists())

    def test_daily_workflow_generates_chat_summary_files_when_enabled(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            private_dir = base / "private"
            private_dir.mkdir()
            holdings = private_dir / "holdings.local.yaml"
            holdings.write_text('funds:\n  - code: "161725"\n    name: "Fund"\n    type: "fund"\n    cost_nav: 1.0\n    amount: 100\n    target_position: 1.0\n', encoding="utf-8")
            config = base / "config.local.yaml"
            config.write_text(
                "\n".join(
                    [
                        "input:",
                        "  mode: holdings_yaml",
                        f"  holdings_yaml: {holdings.as_posix()}",
                        "output:",
                        f"  daily_dir: {(base / 'reports' / 'daily').as_posix()}",
                        f"  latest_dir: {(base / 'reports' / 'private' / 'latest').as_posix()}",
                        "analysis:",
                        "  data_source: mock",
                        "  reporter: offline",
                        "notification:",
                        "  enabled: false",
                        "chat_summary:",
                        "  enabled: true",
                        "  style: wechat",
                        "  max_signals: 3",
                        "  max_warnings: 5",
                    ]
                ),
                encoding="utf-8",
            )
            result = run_daily_workflow(str(config))
            self.assertTrue(result["ok"])
            self.assertTrue((base / "reports" / "private" / "latest" / "chat_summary.txt").exists())

    def test_daily_workflow_does_not_fail_if_chat_summary_generation_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            private_dir = base / "private"
            private_dir.mkdir()
            holdings = private_dir / "holdings.local.yaml"
            holdings.write_text('funds:\n  - code: "161725"\n    name: "Fund"\n    type: "fund"\n    cost_nav: 1.0\n    amount: 100\n    target_position: 1.0\n', encoding="utf-8")
            config = base / "config.local.yaml"
            config.write_text(
                "\n".join(
                    [
                        "input:",
                        "  mode: holdings_yaml",
                        f"  holdings_yaml: {holdings.as_posix()}",
                        "output:",
                        f"  daily_dir: {(base / 'reports' / 'daily').as_posix()}",
                        f"  latest_dir: {(base / 'reports' / 'private' / 'latest').as_posix()}",
                        "analysis:",
                        "  data_source: mock",
                        "  reporter: offline",
                        "notification:",
                        "  enabled: false",
                        "chat_summary:",
                        "  enabled: true",
                    ]
                ),
                encoding="utf-8",
            )
            with mock.patch("asset_analysis.workflow.daily_run.build_chat_summary", side_effect=RuntimeError("boom")):
                result = run_daily_workflow(str(config))
            self.assertTrue(result["ok"])
            self.assertTrue(any("Chat summary generation failed" in item for item in result["warnings"]))

    def test_notification_message_builder_remains_backward_compatible(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            report = _write_report(Path(temp_dir))
            message = build_notification_message(report)
            self.assertIn("signals_summary", message)

    def test_hermes_adapter_remains_backward_compatible(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            holdings = Path(temp_dir) / "holdings.yaml"
            holdings.write_text('funds:\n  - code: "161725"\n    name: "Fund"\n    type: "fund"\n    cost_nav: 1.0\n    amount: 100\n    target_position: 1.0\n', encoding="utf-8")
            result = run_daily_asset_analysis_task(holdings_path=str(holdings), output_dir=str(Path(temp_dir) / "out"))
            self.assertTrue(result["ok"])
            self.assertIn("chat_summary_text", result)

    def test_release_gate_includes_chat_summary_smoke(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_root = Path(temp_dir)
            smoke_dir = output_root / "pipeline_smoke"
            smoke_dir.mkdir()
            report = smoke_dir / "report.json"
            report.write_text(
                json.dumps(
                    {
                        "schema_version": "1.0.0",
                        "generated_at": "2026-05-18T21:00:00+08:00",
                        "run": {"data_source": "mock"},
                        "summary": {"total_profit_rate": 0.0387, "total_profit": 38.7, "total_market_value": 1038.7},
                        "signals": [
                            {
                                "code": "110022",
                                "name": "易方达消费行业股票",
                                "signal": "reduce",
                                "reason": "Current position 84.01% is above target 30.00% by more than the overweight band.",
                            }
                        ],
                        "positions": [{"code": "110022", "name": "易方达消费行业股票", "quote": {"source": "mock", "error": None}}],
                        "portfolio_warnings": ["110022 exceeds max_single_position with current weight 84.01%."],
                        "group_analysis": {"warnings": [], "tag_concentration": []},
                        "schema_errors": [],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            check = run_chat_summary_smoke_check(output_root)
            self.assertTrue(check["ok"])


def _write_report(base: Path) -> Path:
    report = base / "report.json"
    report.write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "generated_at": "2026-05-18T21:00:00+08:00",
                "run": {"data_source": "mock"},
                "summary": {"total_profit_rate": 0.0387, "total_profit": 38.7, "total_market_value": 1038.7},
                "signals": [{"code": "000001", "name": "示例基金", "signal": "add", "reason": "低于目标仓位"}],
                "positions": [{"quote": {"source": "mock", "error": None}}],
                "portfolio_warnings": ["消费集中度过高"],
                "group_analysis": {"warnings": ["消费集中度过高"], "tag_concentration": [{"warnings": ["消费集中度过高"]}]},
                "schema_errors": [],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return report
