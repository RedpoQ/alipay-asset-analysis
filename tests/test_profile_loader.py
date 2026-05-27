import unittest
import tempfile
from pathlib import Path

from asset_analysis.profiles.profile_loader import BUILTIN_PROFILES, load_profile


class ProfileLoaderTests(unittest.TestCase):
    def test_all_built_in_profiles_load(self):
        for path in BUILTIN_PROFILES.values():
            payload = load_profile(path)
            self.assertIn("profile", payload)

    def test_profile_schema_required_fields_validated(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "bad.profile.yaml"
            path.write_text("profile:\n  name: bad\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                load_profile(path)
