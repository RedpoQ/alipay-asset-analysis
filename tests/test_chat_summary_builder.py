import json
import tempfile
import unittest
from pathlib import Path

from asset_analysis.chat_summary.builder import build_chat_summary


class ChatSummaryBuilderTests(unittest.TestCase):
    def test_build_chat_summary_reads_valid_report_json(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            report = _write_report(Path(temp_dir))
            summary = build_chat_summary(str(report))
            self.assertEqual(summary["title"], "每日基金分析")

    def test_build_chat_summary_includes_signals_summary(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            report = _write_report(Path(temp_dir))
            summary = build_chat_summary(str(report))
            self.assertEqual(summary["signals_summary"]["add"], 1)

    def test_build_chat_summary_includes_top_signals_and_warnings(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            report = _write_report(Path(temp_dir))
            summary = build_chat_summary(str(report))
            signal_section = next(item for item in summary["sections"] if item["title"] == "重点信号")
            risk_section = next(item for item in summary["sections"] if item["title"] == "组合风险")
            self.assertTrue(signal_section["items"])
            self.assertTrue(risk_section["items"])

    def test_group_warnings_and_mock_scope_are_included(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            report = _write_report(Path(temp_dir))
            summary = build_chat_summary(str(report))
            self.assertEqual(summary["data_status"]["analysis_scope"], "structure_only")
            self.assertTrue(any("消费集中" in item for section in summary["sections"] for item in section["items"]))

    def test_top_signals_include_localized_reason_fields(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            report = _write_report(Path(temp_dir))
            summary = build_chat_summary(str(report))
            self.assertIn("reason_cn", summary["top_signals"][0])
            self.assertIn("signal_label", summary["top_signals"][0])

    def test_schema_errors_appear_as_warning(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            report = _write_report(Path(temp_dir), schema_errors=["bad"])
            summary = build_chat_summary(str(report))
            self.assertTrue(summary["warnings"])


def _write_report(base: Path, schema_errors: list[str] | None = None) -> Path:
    report = base / "report.json"
    report.write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "generated_at": "2026-05-18T21:00:00+08:00",
                "run": {"data_source": "mock"},
                "summary": {"total_profit_rate": 0.0387, "total_profit": 38.7, "total_market_value": 1038.7},
                "signals": [
                    {
                        "code": "000001",
                        "name": "示例基金",
                        "signal": "add",
                        "reason": "Current position 6.28% is below target 20.00% by more than the rebalance band.",
                    }
                ],
                "positions": [{"quote": {"source": "mock", "error": None}}],
                "portfolio_warnings": ["消费集中度过高"],
                "group_analysis": {"warnings": ["消费集中度过高"], "tag_concentration": [{"warnings": ["消费集中度过高"]}]},
                "schema_errors": schema_errors or [],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return report
