import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from asset_analysis.pipeline import main, run_asset_pipeline


class PipelineTests(unittest.TestCase):
    def test_pipeline_generates_json_and_markdown(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            input_file = base_dir / "holdings.yaml"
            output_dir = base_dir / "latest"
            input_file.write_text(
                """
funds:
  - code: "000001"
    name: "Example Fund"
    type: "fund"
    cost_nav: 1.0
    amount: 100
    target_position: 0.80
stocks:
  - code: "FAIL_STOCK"
    name: "Failure Case"
    type: "stock"
    cost_price: 10
    amount: 10
    target_position: 0.20
""".strip(),
                encoding="utf-8",
            )

            result = run_asset_pipeline(input_file, output_dir, mock_mode=True)

            json_path = output_dir / "report.json"
            md_path = output_dir / "report.md"
            self.assertTrue(json_path.exists())
            self.assertTrue(md_path.exists())
            payload = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertGreater(payload["summary"]["total_cost"], 0)
            self.assertIn("report_md", payload)
            self.assertTrue(any(position["error"] for position in payload["positions"]))
            self.assertTrue(all("quote" in position for position in payload["positions"]))
            self.assertTrue(result.report_md.startswith("# Asset Analysis Report"))
            self.assertIn("## Signals", result.report_md)
            self.assertIn("## Notes / Limitations", result.report_md)

    def test_cli_creates_output_directory_and_prints_paths(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            input_file = base_dir / "holdings.yaml"
            output_dir = base_dir / "nested" / "reports"
            input_file.write_text(
                """
funds:
  - code: "161725"
    name: "Example Fund"
    type: "fund"
    cost_nav: 1.0
    amount: 100
    target_position: 1.0
""".strip(),
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "asset_analysis.pipeline",
                    "--input",
                    str(input_file),
                    "--output",
                    str(output_dir),
                    "--data-source",
                    "mock",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0)
            self.assertTrue(output_dir.exists())
            self.assertTrue((output_dir / "report.json").exists())
            self.assertTrue((output_dir / "report.md").exists())
            self.assertIn("Generated JSON report:", completed.stdout)
            self.assertIn("Generated Markdown report:", completed.stdout)

    def test_main_returns_non_zero_on_invalid_input(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            input_file = base_dir / "invalid.yaml"
            output_dir = base_dir / "reports"
            input_file.write_text("funds:\n  code: broken", encoding="utf-8")

            exit_code = main(["--input", str(input_file), "--output", str(output_dir)])

            self.assertEqual(exit_code, 1)
            self.assertFalse((output_dir / "report.json").exists())
