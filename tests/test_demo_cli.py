import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from asset_analysis.demo.cli import main as demo_cli_main
from asset_analysis.pipeline import run_asset_pipeline


class DemoCliTests(unittest.TestCase):
    def test_cli_works_with_source_report(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            source_dir = base / "source"
            output_dir = base / "demo"
            run_asset_pipeline("examples/real_existing_holdings.yaml", source_dir, data_source="mock", reporter_mode="offline")
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = demo_cli_main(
                    ["--source", str(source_dir / "report.json"), "--output", str(output_dir), "--mode", "public", "--force"]
                )
            self.assertEqual(exit_code, 0)
            payload = json.loads(buffer.getvalue())
            self.assertTrue(payload["ok"])

    def test_cli_works_with_builtin_demo(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "demo"
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = demo_cli_main(["--output", str(output_dir), "--mode", "realistic_demo", "--force"])
            self.assertEqual(exit_code, 0)
            payload = json.loads(buffer.getvalue())
            self.assertTrue(payload["ok"])


if __name__ == "__main__":
    unittest.main()
