import unittest
from pathlib import Path

from asset_analysis.release.checks import check_docs_release_package
from asset_analysis.release.gate import run_release_gate


class DocsReleasePackageTests(unittest.TestCase):
    def test_required_docs_exist(self):
        for path in [
            "docs/QUICK_START.md",
            "docs/DAILY_WORKFLOW.md",
            "docs/HERMES_INTEGRATION.md",
            "docs/CONFIG_REFERENCE.md",
            "docs/PRIVACY_AND_SAFETY.md",
            "docs/MODULE_INDEX.md",
            "docs/RELEASE_CHECKLIST.md",
            "CHANGELOG.md",
            "RELEASE_NOTES_v0.1.0-local.md",
            "VERSION",
        ]:
            self.assertTrue(Path(path).exists(), path)

    def test_readme_references_release_and_quick_start(self):
        content = Path("README.md").read_text(encoding="utf-8")
        self.assertIn("v0.1.0-local", content)
        self.assertIn("docs/QUICK_START.md", content)

    def test_privacy_doc_mentions_private_and_gitignore(self):
        content = Path("docs/PRIVACY_AND_SAFETY.md").read_text(encoding="utf-8")
        self.assertIn("private/", content)
        self.assertIn(".gitignore", content)

    def test_hermes_integration_says_no_direct_analysis(self):
        content = Path("docs/HERMES_INTEGRATION.md").read_text(encoding="utf-8")
        self.assertIn("Hermes must not analyze funds directly", content)

    def test_release_notes_cover_core_safety_limits(self):
        content = Path("RELEASE_NOTES_v0.1.0-local.md").read_text(encoding="utf-8")
        self.assertIn("no prediction", content)
        self.assertIn("no automatic trading", content)

    def test_version_file_matches_release(self):
        self.assertEqual(Path("VERSION").read_text(encoding="utf-8").strip(), "v0.1.0-local")

    def test_release_gate_includes_docs_check(self):
        result = run_release_gate(output_dir="reports/test_docs_release_gate", skip_tests=True, no_smoke=True, json_only=True)
        check_names = [item["name"] for item in result["checks"]]
        self.assertIn("docs_release_package", check_names)

    def test_docs_release_package_check_passes(self):
        result = check_docs_release_package()
        self.assertTrue(result["ok"])
