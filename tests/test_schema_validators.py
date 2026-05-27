import unittest

from asset_analysis.schema.adapter_schema import merge_adapter_contract
from asset_analysis.schema.constants import ASSET_ANALYSIS_SCHEMA_VERSION
from asset_analysis.schema.validators import validate_adapter_result_schema, validate_report_schema


class SchemaValidatorTests(unittest.TestCase):
    def test_valid_pipeline_report_passes_validate_report_schema(self):
        payload = {
            "schema_version": ASSET_ANALYSIS_SCHEMA_VERSION,
            "generated_at": "2026-05-18T00:00:00+00:00",
            "run": {"input": "a", "output_dir": "b", "data_source": "mock", "rules_source": "default", "reporter_mode": "offline"},
            "summary": {},
            "positions": [{"code": "A", "name": "Asset", "type": "fund", "cost": 1, "market_value": 1, "profit": 0, "profit_rate": 0, "target_position": 0.5, "current_position": 0.5, "quote": {}, "group": "other", "tags": []}],
            "signals": [{"code": "A", "name": "Asset", "type": "fund", "signal": "hold", "confidence": "low", "severity": "normal", "reason": "x", "reasons": [], "warnings": [], "blocked_by": []}],
            "portfolio_warnings": [],
            "group_analysis": {},
            "rules": {},
            "reporter": {},
            "recommendations": [],
            "report_md": "x",
        }
        self.assertEqual(validate_report_schema(payload), [])

    def test_missing_required_report_fields_returns_schema_errors(self):
        payload = {"schema_version": ASSET_ANALYSIS_SCHEMA_VERSION}
        self.assertTrue(validate_report_schema(payload))

    def test_valid_openclaw_adapter_result_passes_validate_adapter_result_schema(self):
        result = merge_adapter_contract(
            {
                "ok": True,
                "report_json": "a",
                "report_md": "b",
                "summary": {},
                "signals": [],
                "portfolio_warnings": [],
                "reporter": {},
                "errors": [],
                "warnings": [],
                "schema_errors": [],
            }
        )
        self.assertEqual(validate_adapter_result_schema(result), [])

    def test_valid_hermes_adapter_result_passes_validate_adapter_result_schema(self):
        result = merge_adapter_contract(
            {
                "ok": True,
                "task": "daily_asset_analysis",
                "report_json": "a",
                "report_md": "b",
                "summary": {},
                "signals_summary": {"add": 0, "reduce": 0, "hold": 0},
                "top_signals": [],
                "portfolio_warnings": [],
                "reporter": {},
                "daily_message": "",
                "errors": [],
                "warnings": [],
                "schema_errors": [],
            }
        )
        self.assertEqual(validate_adapter_result_schema(result), [])
