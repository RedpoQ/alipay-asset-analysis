import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from asset_analysis.ux.paths import find_project_root
from asset_analysis.workflow.daily_run import main as daily_run_main


class SingleChannelWorkflowTests(unittest.TestCase):
    def test_workflow_json_mode_still_works(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            private_dir = base / "private"
            private_dir.mkdir()
            csv = private_dir / "alipay_holdings.local.csv"
            csv.write_text(Path("private/alipay_holdings.local.example.csv").read_text(encoding="utf-8"), encoding="utf-8")
            config = base / "config.local.yaml"
            config.write_text(
                "\n".join(
                    [
                        "profile:",
                        "  name: balanced",
                        "  file: examples/profiles/balanced.profile.yaml",
                        "input:",
                        "  mode: alipay_csv",
                        f"  alipay_csv: {csv.as_posix()}",
                        f"  holdings_yaml: {(private_dir / 'holdings.local.yaml').as_posix()}",
                        "output:",
                        f"  daily_dir: {(base / 'reports' / 'daily').as_posix()}",
                        f"  latest_dir: {(base / 'reports' / 'private' / 'latest').as_posix()}",
                        "analysis:",
                        "  data_source: mock",
                        "  reporter: offline",
                        "notification:",
                        "  enabled: false",
                        "  dry_run: true",
                    ]
                ),
                encoding="utf-8",
            )
            sink = io.StringIO()
            with redirect_stdout(sink):
                code = daily_run_main(["--config", str(config), "--json-only"])
            self.assertEqual(code, 0)
            payload = json.loads(sink.getvalue())
            self.assertTrue(payload["ok"])

    def test_daily_script_path_helper_finds_project_root(self):
        root = find_project_root(Path("scripts/daily_run.py").resolve())
        self.assertTrue((root / "asset_analysis").exists())
