import json
import tempfile
import unittest
from pathlib import Path

from asset_analysis.hermes.result_reader import build_failure_message, read_chat_summary, read_latest_result


class HermesResultReaderTests(unittest.TestCase):
    def test_read_chat_summary_reads_text(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "chat_summary.txt"
            path.write_text("规则驱动，不预测。", encoding="utf-8")
            self.assertEqual(read_chat_summary(path), "规则驱动，不预测。")

    def test_read_latest_result_reads_known_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            (base / "chat_summary.txt").write_text("summary", encoding="utf-8")
            (base / "report.json").write_text(json.dumps({"ok": True}, ensure_ascii=False), encoding="utf-8")
            (base / "preflight_report.json").write_text(json.dumps({"ok": True}, ensure_ascii=False), encoding="utf-8")
            payload = read_latest_result(base)
            self.assertEqual(payload["chat_summary_path"], str(base / "chat_summary.txt"))
            self.assertEqual(payload["report_payload"]["ok"], True)
            self.assertEqual(payload["preflight_payload"]["ok"], True)

    def test_failure_message_does_not_invent_fund_analysis(self):
        result = {
            "ok": False,
            "errors": [{"stage": "setup", "message": "Config not found: private/config.local.yaml"}],
        }
        message = build_failure_message(result)
        self.assertIn("Fix command", message)
        self.assertIn("No fund analysis was generated manually.", message)
        self.assertNotIn("可补仓", message)


if __name__ == "__main__":
    unittest.main()
