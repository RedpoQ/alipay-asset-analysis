import tempfile
import unittest
from pathlib import Path

from asset_analysis.onboarding.init_project import init_local_project


class OnboardingInitTests(unittest.TestCase):
    def _prepare_templates(self, base: Path) -> None:
        (base / "private").mkdir(parents=True, exist_ok=True)
        (base / "examples" / "profiles").mkdir(parents=True, exist_ok=True)
        for source, target in [
            ("private/alipay_holdings.local.example.csv", base / "private" / "alipay_holdings.local.example.csv"),
            ("private/manual_quotes.local.example.csv", base / "private" / "manual_quotes.local.example.csv"),
            ("private/holdings.local.example.yaml", base / "private" / "holdings.local.example.yaml"),
            ("examples/profiles/balanced.profile.yaml", base / "examples" / "profiles" / "balanced.profile.yaml"),
        ]:
            target.write_text(Path(source).read_text(encoding="utf-8"), encoding="utf-8")

    def test_init_project_creates_missing_private_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            self._prepare_templates(base)
            result = init_local_project(project_root=base, profile="balanced", data_source="mock")
            self.assertTrue(result["ok"])
            self.assertTrue((base / "private" / "config.local.yaml").exists())
            self.assertTrue((base / "private" / "alipay_holdings.local.csv").exists())
            self.assertTrue((base / "private" / "manual_quotes.local.csv").exists())
            self.assertTrue((base / "private" / "holdings.local.yaml").exists())

    def test_init_project_does_not_overwrite_without_force(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            self._prepare_templates(base)
            target = base / "private" / "config.local.yaml"
            target.write_text("custom: true\n", encoding="utf-8")
            result = init_local_project(project_root=base, profile="balanced", data_source="manual")
            self.assertIn(str(target), result["skipped"])
            self.assertEqual(target.read_text(encoding="utf-8"), "custom: true\n")


if __name__ == "__main__":
    unittest.main()
