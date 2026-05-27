import json
import tempfile
import unittest
from pathlib import Path

from asset_analysis.preflight.cli import main


class PreflightCliTests(unittest.TestCase):
    def test_cli_writes_reports(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            holdings = base / "holdings.yaml"
            holdings.write_text(
                'funds:\n  - code: "000001"\n    name: "Fund"\n    type: "fund"\n    cost_nav: 1.0\n    amount: 100\n    target_position: 0.5\n',
                encoding="utf-8",
            )
            config = base / "config.local.yaml"
            json_output = base / "preflight_report.json"
            md_output = base / "preflight_report.md"
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
            result = main(["--config", str(config), "--output", str(json_output), "--markdown", str(md_output)])
            self.assertEqual(result, 0)
            self.assertTrue(json_output.exists())
            self.assertTrue(md_output.exists())
            payload = json.loads(json_output.read_text(encoding="utf-8"))
            self.assertTrue(payload["ok"])
