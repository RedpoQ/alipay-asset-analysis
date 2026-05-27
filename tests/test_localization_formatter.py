import unittest

from asset_analysis.localization.formatter import localize_data_status


class LocalizationFormatterTests(unittest.TestCase):
    def test_mock_data_status_is_structure_only(self):
        status = localize_data_status("mock", [{"quote": {"source": "mock", "error": None}}], schema_errors=[])
        self.assertEqual(status["analysis_scope"], "structure_only")
        self.assertIn("当前使用 mock 数据", status["limitations"][0])

    def test_schema_errors_appear_in_data_status(self):
        status = localize_data_status("mock", [{"quote": {"source": "mock", "error": None}}], schema_errors=["bad"])
        self.assertTrue(any("结构校验问题" in item for item in status["limitations"]))
