import tempfile
import unittest
from pathlib import Path

from asset_analysis.workflow.daily_run import run_daily_workflow


class DailyWorkflowPreflightTests(unittest.TestCase):
    def _write_config(self, base: Path, holdings_path: Path, lines_extra: list[str] | None = None) -> Path:
        config = base / "config.local.yaml"
        lines = [
            "input:",
            "  mode: holdings_yaml",
            f"  holdings_yaml: {holdings_path.as_posix()}",
            "output:",
            f"  daily_dir: {(base / 'reports' / 'daily').as_posix()}",
            f"  latest_dir: {(base / 'reports' / 'private' / 'latest').as_posix()}",
            "analysis:",
            "  data_source: mock",
            "  reporter: offline",
            "notification:",
            "  enabled: false",
            "  dry_run: true",
            "preflight:",
            "  enabled: true",
            "  strict_quotes: false",
            "  fail_on_stale_quotes: false",
            "  fail_on_duplicate_codes: false",
        ]
        if lines_extra:
            lines.extend(lines_extra)
        config.write_text("\n".join(lines), encoding="utf-8")
        return config

    def test_daily_workflow_runs_preflight_first(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            holdings = base / "holdings.yaml"
            holdings.write_text(
                'funds:\n  - code: "000001"\n    name: "Fund"\n    type: "fund"\n    cost_nav: 1.0\n    amount: 100\n    target_position: 0.5\n',
                encoding="utf-8",
            )
            config = self._write_config(base, holdings)
            result = run_daily_workflow(str(config))
            self.assertTrue(result["ok"])
            self.assertIsNotNone(result["preflight"])

    def test_daily_workflow_stops_on_critical_preflight_failure(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            holdings = base / "missing.yaml"
            config = self._write_config(base, holdings)
            result = run_daily_workflow(str(config))
            self.assertFalse(result["ok"])
            self.assertIsNone(result["report_json"])
            self.assertIsNotNone(result["preflight"])

    def test_daily_workflow_continues_on_warning_only_preflight(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            holdings = base / "holdings.yaml"
            holdings.write_text(
                'funds:\n  - code: "000001"\n    name: "Fund A"\n    type: "fund"\n    cost_nav: 1.0\n    amount: 100\n    target_position: 0.2\n  - code: "000001"\n    name: "Fund B"\n    type: "fund"\n    cost_nav: 1.1\n    amount: 50\n    target_position: 0.2\n',
                encoding="utf-8",
            )
            config = self._write_config(base, holdings)
            result = run_daily_workflow(str(config))
            self.assertTrue(result["ok"])
            self.assertTrue(any("重复持仓代码" in item for item in result["warnings"]))
            chat_summary = Path(result["report_json"]).with_name("chat_summary.txt").read_text(encoding="utf-8")
            self.assertIn("数据检查发现", chat_summary)

    def test_preflight_reports_copied_to_latest(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            holdings = base / "holdings.yaml"
            holdings.write_text(
                'funds:\n  - code: "000001"\n    name: "Fund"\n    type: "fund"\n    cost_nav: 1.0\n    amount: 100\n    target_position: 0.5\n',
                encoding="utf-8",
            )
            config = self._write_config(base, holdings)
            result = run_daily_workflow(str(config))
            latest_dir = Path(result["latest_dir"])
            self.assertTrue((latest_dir / "preflight_report.json").exists())
            self.assertTrue((latest_dir / "preflight_report.md").exists())
