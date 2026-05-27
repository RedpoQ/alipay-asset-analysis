import json
import tempfile
import unittest
from pathlib import Path

from asset_analysis.ux.daily_console import format_daily_console_output


class DailyConsoleTests(unittest.TestCase):
    def test_console_formatter_includes_pass_blocked(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            latest = Path(temp_dir)
            (latest / "chat_summary.json").write_text(json.dumps({"one_line": "收益率 3.87%。"}, ensure_ascii=False), encoding="utf-8")
            (latest / "preflight_report.md").write_text("# preflight\n", encoding="utf-8")
            result = {
                "ok": True,
                "latest_dir": str(latest),
                "profile": {"name": "balanced", "display_name": "平衡型"},
                "preflight": {"ok": True, "summary": {"warnings": 2}},
                "effective_config": str(latest / "effective_config.json"),
                "warnings": [],
            }
            (latest / "effective_config.json").write_text(json.dumps({"analysis": {"data_source": "manual"}}, ensure_ascii=False), encoding="utf-8")
            text = format_daily_console_output(result)
            self.assertIn("Daily Asset Analysis: PASS", text)

    def test_console_formatter_includes_chat_summary_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            latest = Path(temp_dir)
            (latest / "chat_summary.json").write_text(json.dumps({"one_line": "收益率 3.87%。"}, ensure_ascii=False), encoding="utf-8")
            (latest / "effective_config.json").write_text(json.dumps({"analysis": {"data_source": "mock"}}, ensure_ascii=False), encoding="utf-8")
            result = {
                "ok": False,
                "latest_dir": str(latest),
                "profile": {"name": "balanced"},
                "preflight": {"ok": False, "summary": {"warnings": 0}},
                "effective_config": str(latest / "effective_config.json"),
                "warnings": [],
            }
            text = format_daily_console_output(result)
            self.assertIn("BLOCKED", text)
            self.assertIn("chat_summary.txt", text)
