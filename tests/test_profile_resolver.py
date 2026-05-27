import tempfile
import unittest
from pathlib import Path

from asset_analysis.profiles.profile_loader import BUILTIN_PROFILES
from asset_analysis.profiles.resolver import resolve_profile_config


class ProfileResolverTests(unittest.TestCase):
    def test_missing_profile_returns_structured_error(self):
        result = resolve_profile_config({}, profile_path="missing.profile.yaml")
        self.assertTrue(result["errors"])

    def test_explicit_local_config_overrides_profile_value(self):
        result = resolve_profile_config(
            {
                "analysis": {"data_source": "manual", "quotes": "private/manual_quotes.local.csv"},
                "chat_summary": {"max_signals": 9},
            },
            profile_path=BUILTIN_PROFILES["balanced"],
        )
        self.assertFalse(result["errors"])
        self.assertEqual(result["effective_config"]["analysis"]["data_source"], "manual")
        self.assertEqual(result["effective_config"]["chat_summary"]["max_signals"], 9)

    def test_resolver_validates_referenced_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            profile = base / "bad.profile.yaml"
            profile.write_text(
                "\n".join(
                    [
                        "profile:",
                        '  name: bad',
                        '  display_name: 坏模板',
                        '  version: "1.0.0"',
                        '  description: "bad"',
                        "analysis:",
                        "  rules: missing.rules.yaml",
                        "preflight:",
                        "  strict_quotes: false",
                        "chat_summary:",
                        "  style: wechat",
                    ]
                ),
                encoding="utf-8",
            )
            result = resolve_profile_config({}, profile_path=str(profile))
            self.assertTrue(result["errors"])
