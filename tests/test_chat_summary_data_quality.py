import json
import tempfile
import unittest
from pathlib import Path

from asset_analysis.chat_summary.builder import build_chat_summary
from asset_analysis.pipeline import main as pipeline_main


class ChatSummaryDataQualityTests(unittest.TestCase):
    def test_chat_summary_includes_manual_data_status(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            holdings = base / "holdings.yaml"
            output_dir = base / "reports"
            holdings.write_text(Path("examples/real_existing_holdings.yaml").read_text(encoding="utf-8"), encoding="utf-8")
            pipeline_main(
                [
                    "--input",
                    str(holdings),
                    "--output",
                    str(output_dir),
                    "--data-source",
                    "manual",
                    "--quotes",
                    "examples/manual_quotes.example.csv",
                    "--reporter",
                    "offline",
                ]
            )
            summary = build_chat_summary(str(output_dir / "report.json"))
            data_section = next(item for item in summary["sections"] if item["title"] == "数据状态")
            self.assertTrue(any("手工净值数据" in item for item in data_section["items"]))

    def test_chat_summary_includes_stale_warning(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            report = base / "report.json"
            report.write_text(
                json.dumps(
                    {
                        "schema_version": "1.0.0",
                        "generated_at": "2026-05-18T21:00:00+08:00",
                        "run": {"data_source": "manual"},
                        "summary": {"total_profit_rate": 0.01, "total_profit": 1.0, "total_market_value": 100.0},
                        "signals": [],
                        "positions": [],
                        "portfolio_warnings": [],
                        "group_analysis": {"warnings": [], "tag_concentration": []},
                        "exposure_analysis": {"warnings": [], "risk_notes": []},
                        "data_quality": {
                            "data_source": "manual",
                            "has_realtime_quote": False,
                            "analysis_scope": "manual_quote",
                            "quote_count": 1,
                            "missing_quote_count": 0,
                            "stale_quote_count": 1,
                            "fresh_quote_count": 0,
                            "warnings": ["000001 的净值/报价日期已过期。"],
                            "limitations": ["部分净值数据已过期，今日结果更适合做结构检查，不适合做短线判断。"],
                        },
                        "rules": {},
                        "reporter": {},
                        "recommendations": [],
                        "report_md": "",
                        "schema_errors": [],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            summary = build_chat_summary(str(report))
            data_section = next(item for item in summary["sections"] if item["title"] == "数据状态")
            self.assertTrue(any("已过期" in item for item in data_section["items"]))
