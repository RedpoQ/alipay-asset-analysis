import json
import tempfile
import unittest
from pathlib import Path

from asset_analysis.chat_summary.builder import build_chat_summary
from asset_analysis.chat_summary.cli import main as chat_summary_main
from asset_analysis.notifications.message_builder import build_notification_message
from asset_analysis.release.checks import run_chat_summary_smoke_check


class ChatSummaryLocalizedTests(unittest.TestCase):
    def test_chat_summary_txt_avoids_common_raw_english_rule_phrases(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            report = _write_report(base)
            txt_path = base / "chat_summary.txt"
            code = chat_summary_main(["--report", str(report), "--output", str(txt_path)])
            self.assertEqual(code, 0)
            content = txt_path.read_text(encoding="utf-8")
            self.assertNotIn("Current position", content)
            self.assertNotIn("exceeds max_single_position", content)
            self.assertIn("规则驱动", content)
            self.assertIn("不预测", content)

    def test_chat_summary_json_includes_reason_and_reason_cn(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            summary = build_chat_summary(str(_write_report(Path(temp_dir))))
            top_signal = summary["top_signals"][0]
            self.assertIn("reason", top_signal)
            self.assertIn("reason_cn", top_signal)
            self.assertIn("signal_label", top_signal)
            self.assertTrue(summary["warnings_localized"])

    def test_notification_message_builder_remains_backward_compatible(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            report = _write_report(base)
            chat_summary = build_chat_summary(str(report))
            (base / "chat_summary.json").write_text(json.dumps(chat_summary, ensure_ascii=False, indent=2), encoding="utf-8")
            (base / "chat_summary.txt").write_text(chat_summary["text"], encoding="utf-8")
            message = build_notification_message(report)
            self.assertIn("signals_summary", message)
            self.assertIn("规则驱动", message["summary"])

    def test_release_gate_chat_summary_smoke_checks_localization(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_root = Path(temp_dir)
            smoke_dir = output_root / "pipeline_smoke"
            smoke_dir.mkdir(parents=True)
            report = _write_report(smoke_dir)
            report.rename(smoke_dir / "report.json")
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
                "summary": {"total_profit_rate": 0.0387, "total_profit": 239.59, "total_market_value": 6427.27},
                "signals": [
                    {
                        "code": "161725",
                        "name": "招商中证白酒指数(LOF)A",
                        "type": "fund",
                        "signal": "add",
                        "reason": "Current position 6.28% is below target 20.00% by more than the rebalance band.",
                    },
                    {
                        "code": "110022",
                        "name": "易方达消费行业股票",
                        "type": "fund",
                        "signal": "reduce",
                        "reason": "Current position 84.01% is above target 30.00% by more than the overweight band.",
                    },
                ],
                "positions": [
                    {"code": "161725", "name": "招商中证白酒指数(LOF)A", "quote": {"source": "mock", "error": None}},
                    {"code": "110022", "name": "易方达消费行业股票", "quote": {"source": "mock", "error": None}},
                ],
                "portfolio_warnings": [
                    "110022 exceeds max_single_position with current weight 84.01%.",
                    "Total fund position 100.00% exceeds max_fund_position 80.00%.",
                ],
                "group_analysis": {
                    "warnings": ["Group sector_theme current position 35.00% exceeds max_position 30.00%."],
                    "groups": [
                        {
                            "group": "sector_theme",
                            "current_position": 0.35,
                            "target_position": 0.2,
                            "warnings": ["Group sector_theme current position 35.00% exceeds max_position 30.00%."],
                        }
                    ],
                    "tag_concentration": [
                        {"warnings": ["Tag 消费 concentration 45.00% exceeds configured threshold 30.00%."]}
                    ],
                },
                "schema_errors": [],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return report
