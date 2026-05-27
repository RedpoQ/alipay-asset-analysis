import tempfile
import unittest
from pathlib import Path

from asset_analysis.preflight.checks import run_preflight
from asset_analysis.workflow.config import load_workflow_config


class PreflightConfigCheckTests(unittest.TestCase):
    def test_config_example_loads_with_preflight(self):
        config = load_workflow_config("private/config.local.example.yaml")
        self.assertTrue(config.preflight.enabled)
        self.assertFalse(config.preflight.strict_quotes)

    def test_config_safety_detects_reporter_offline(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            holdings = base / "holdings.yaml"
            holdings.write_text(
                'funds:\n  - code: "000001"\n    name: "Fund"\n    type: "fund"\n    cost_nav: 1.0\n    amount: 100\n    target_position: 0.5\n',
                encoding="utf-8",
            )
            config = base / "config.local.yaml"
            config.write_text(
                "\n".join(
                    [
                        "input:",
                        "  mode: holdings_yaml",
                        f"  holdings_yaml: {holdings.as_posix()}",
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
                    ]
                ),
                encoding="utf-8",
            )
            result = run_preflight(str(config))
            check = next(item for item in result["checks"] if item["name"] == "reporter_offline")
            self.assertTrue(check["ok"])

    def test_config_safety_warns_when_llm_reporter_enabled(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            holdings = base / "holdings.yaml"
            holdings.write_text(
                'funds:\n  - code: "000001"\n    name: "Fund"\n    type: "fund"\n    cost_nav: 1.0\n    amount: 100\n    target_position: 0.5\n',
                encoding="utf-8",
            )
            config = base / "config.local.yaml"
            config.write_text(
                "\n".join(
                    [
                        "input:",
                        "  mode: holdings_yaml",
                        f"  holdings_yaml: {holdings.as_posix()}",
                        "output:",
                        f"  daily_dir: {(base / 'reports' / 'daily').as_posix()}",
                        f"  latest_dir: {(base / 'reports' / 'private' / 'latest').as_posix()}",
                        "analysis:",
                        "  data_source: mock",
                        "  reporter: llm",
                        "notification:",
                        "  enabled: false",
                        "  dry_run: true",
                        "preflight:",
                        "  enabled: true",
                    ]
                ),
                encoding="utf-8",
            )
            result = run_preflight(str(config))
            check = next(item for item in result["checks"] if item["name"] == "llm_reporter_notice")
            self.assertFalse(check["ok"])
