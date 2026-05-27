import json
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest import mock

from asset_analysis.release.gate import run_release_gate


class ReleaseGateTests(unittest.TestCase):
    def test_release_gate_result_schema_is_json_serializable(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            result = run_release_gate(output_dir=temp_dir, skip_tests=True, no_smoke=True)
            json.dumps(result, ensure_ascii=False)

    def test_warning_check_does_not_fail_whole_gate(self):
        with mock.patch("asset_analysis.release.gate.run_history_smoke_check", return_value={"name": "history_smoke", "ok": False, "severity": "warning", "message": "warn", "details": {}}):
            with tempfile.TemporaryDirectory() as temp_dir:
                result = run_release_gate(output_dir=temp_dir, skip_tests=True, no_smoke=False)
                self.assertTrue(result["ok"])

    def test_critical_check_fails_gate(self):
        with mock.patch("asset_analysis.release.gate.check_required_files", return_value={"name": "required_files", "ok": False, "severity": "critical", "message": "bad", "details": {}}):
            with tempfile.TemporaryDirectory() as temp_dir:
                result = run_release_gate(output_dir=temp_dir, skip_tests=True, no_smoke=True)
                self.assertFalse(result["ok"])

    def test_markdown_report_is_generated(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            result = run_release_gate(output_dir=temp_dir, skip_tests=True, no_smoke=True)
            self.assertTrue(Path(result["report_json"]).exists())
            self.assertTrue(Path(result["report_md"]).exists())

    def test_no_smoke_path_works(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            result = run_release_gate(output_dir=temp_dir, skip_tests=True, no_smoke=True)
            self.assertTrue(result["ok"])
            smoke_names = [item["name"] for item in result["checks"] if "smoke" in item["name"]]
            self.assertEqual(smoke_names, [])

    def test_smoke_test_helpers_are_mockable(self):
        smoke_ok = {"name": "pipeline_smoke", "ok": True, "severity": "critical", "message": "ok", "details": {}}
        with ExitStack() as stack:
            for target, value in [
                ("asset_analysis.release.gate.run_pipeline_smoke_check", smoke_ok),
                ("asset_analysis.release.gate.check_hermes_prompt_templates", {**smoke_ok, "name": "hermes_prompt_templates"}),
                ("asset_analysis.release.gate.run_profile_files_check", {**smoke_ok, "name": "profile_files"}),
                ("asset_analysis.release.gate.run_profile_loader_check", {**smoke_ok, "name": "profile_loader"}),
                ("asset_analysis.release.gate.run_profile_resolver_check", {**smoke_ok, "name": "profile_resolver"}),
                ("asset_analysis.release.gate.run_manual_quote_smoke_check", {**smoke_ok, "name": "manual_quote_smoke"}),
                ("asset_analysis.release.gate.run_preflight_smoke_check", {**smoke_ok, "name": "preflight_smoke"}),
                ("asset_analysis.release.gate.run_profile_workflow_smoke_check", {**smoke_ok, "name": "profile_workflow_smoke"}),
                ("asset_analysis.release.gate.run_setup_check_smoke_check", {**smoke_ok, "name": "setup_check_smoke"}),
                ("asset_analysis.release.gate.run_onboarding_init_smoke_check", {**smoke_ok, "name": "onboarding_init_smoke"}),
                ("asset_analysis.release.gate.run_alipay_preview_smoke_check", {**smoke_ok, "name": "alipay_preview_smoke"}),
                ("asset_analysis.release.gate.run_setup_repair_hints_smoke_check", {**smoke_ok, "name": "setup_repair_hints_smoke"}),
                ("asset_analysis.release.gate.run_hermes_cronjob_runner_smoke_check", {**smoke_ok, "name": "hermes_cronjob_runner_smoke"}),
                ("asset_analysis.release.gate.run_demo_bundle_smoke_check", {**smoke_ok, "name": "demo_bundle_smoke"}),
                ("asset_analysis.release.gate.run_daily_workflow_smoke_check", {**smoke_ok, "name": "daily_workflow_smoke"}),
                ("asset_analysis.release.gate.run_notify_dry_run_smoke_check", {**smoke_ok, "name": "notify_dry_run_smoke"}),
                ("asset_analysis.release.gate.run_notification_orchestrator_dry_run_smoke_check", {**smoke_ok, "name": "notification_orchestrator_dry_run_smoke"}),
                ("asset_analysis.release.gate.run_chat_summary_smoke_check", {**smoke_ok, "name": "chat_summary_smoke"}),
                ("asset_analysis.release.gate.run_openclaw_smoke_check", {**smoke_ok, "name": "openclaw_smoke"}),
                ("asset_analysis.release.gate.run_hermes_smoke_check", {**smoke_ok, "name": "hermes_smoke"}),
                ("asset_analysis.release.gate.run_history_smoke_check", {"name": "history_smoke", "ok": True, "severity": "warning", "message": "ok", "details": {}}),
            ]:
                stack.enter_context(mock.patch(target, return_value=value))
            with tempfile.TemporaryDirectory() as temp_dir:
                result = run_release_gate(output_dir=temp_dir, skip_tests=True, no_smoke=False)
                self.assertTrue(result["ok"])
