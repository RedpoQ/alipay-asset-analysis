import json
import tempfile
import unittest
from pathlib import Path

from asset_analysis.demo.bundle import build_demo_bundle, scan_demo_bundle_output


class DemoBundleTests(unittest.TestCase):
    def test_demo_bundle_writes_expected_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "demo"
            result = build_demo_bundle(output_dir=str(output_dir), mode="realistic_demo")
            self.assertTrue(result["ok"])
            self.assertTrue((output_dir / "demo_report.json").exists())
            self.assertTrue((output_dir / "demo_chat_summary.txt").exists())
            self.assertTrue((output_dir / "README_DEMO.md").exists())

    def test_demo_bundle_scan_catches_sensitive_strings(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "demo"
            output_dir.mkdir(parents=True, exist_ok=True)
            (output_dir / "bad.txt").write_text("C:/Users/demo/private/config.local.yaml", encoding="utf-8")
            findings = scan_demo_bundle_output(output_dir)
            self.assertIn("C:/Users/", findings)

    def test_readme_demo_is_generated(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "demo"
            result = build_demo_bundle(output_dir=str(output_dir), mode="public")
            self.assertTrue(result["ok"])
            content = (output_dir / "README_DEMO.md").read_text(encoding="utf-8")
            self.assertIn("What This Demo Shows", content)


if __name__ == "__main__":
    unittest.main()
