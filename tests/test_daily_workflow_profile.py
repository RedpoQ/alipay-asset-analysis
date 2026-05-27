import json
import tempfile
import unittest
from pathlib import Path

from asset_analysis.workflow.daily_run import run_daily_workflow


class DailyWorkflowProfileTests(unittest.TestCase):
    def test_daily_workflow_loads_profile(self):
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
                        "profile:",
                        "  name: balanced",
                        "  file: examples/profiles/balanced.profile.yaml",
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
            result = run_daily_workflow(str(config))
            self.assertTrue(result["ok"])
            self.assertEqual(result["profile"]["name"], "balanced")

    def test_daily_workflow_writes_effective_config(self):
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
                        "profile:",
                        "  name: balanced",
                        "  file: examples/profiles/balanced.profile.yaml",
                        "input:",
                        "  mode: holdings_yaml",
                        f"  holdings_yaml: {holdings.as_posix()}",
                        "output:",
                        f"  daily_dir: {(base / 'reports' / 'daily').as_posix()}",
                        f"  latest_dir: {(base / 'reports' / 'private' / 'latest').as_posix()}",
                        "analysis:",
                        "  data_source: manual",
                        "  reporter: offline",
                        f"  quotes: {(base / 'quotes.csv').as_posix()}",
                        "notification:",
                        "  enabled: false",
                        "  dry_run: true",
                        "preflight:",
                        "  enabled: false",
                    ]
                ),
                encoding="utf-8",
            )
            (base / "quotes.csv").write_text(
                "code,name,type,current_nav,current_price,as_of,source,currency,notes\n000001,Fund,fund,1.2,,2026-05-19,manual_nav,CNY,\n",
                encoding="utf-8",
            )
            result = run_daily_workflow(str(config))
            self.assertTrue(result["ok"])
            effective_path = Path(result["effective_config"])
            self.assertTrue(effective_path.exists())
            payload = json.loads(effective_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["analysis"]["data_source"], "manual")
