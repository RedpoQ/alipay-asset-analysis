import unittest

from asset_analysis.chat_summary.formatter import format_chat_summary


class ChatSummaryFormatterTests(unittest.TestCase):
    def test_formatter_text_output_is_wechat_friendly(self):
        summary = {
            "title": "每日基金分析",
            "one_line": "收益率 3.87%，规则驱动，不预测。",
            "sections": [{"title": "总览", "items": ["总收益率：3.87%"]}],
        }
        output = format_chat_summary(summary, format="text")
        self.assertIn("每日基金分析", output)
        self.assertNotIn("|", output)

    def test_formatter_markdown_output_works(self):
        summary = {
            "title": "每日基金分析",
            "one_line": "收益率 3.87%，规则驱动，不预测。",
            "sections": [{"title": "总览", "items": ["总收益率：3.87%"]}],
        }
        output = format_chat_summary(summary, format="markdown")
        self.assertIn("# 每日基金分析", output)
        self.assertIn("## 总览", output)
