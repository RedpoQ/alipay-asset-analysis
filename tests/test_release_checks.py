import tempfile
import unittest
from pathlib import Path
from unittest import mock

from asset_analysis.release.checks import (
    check_default_safety_config,
    check_docs_release_package,
    check_gitignore_privacy,
    check_required_files,
    check_schema_constants,
    run_python_tests_check,
)


class ReleaseChecksTests(unittest.TestCase):
    def test_required_files_check_works(self):
        result = check_required_files()
        self.assertTrue(result["ok"])

    def test_gitignore_privacy_patterns_check_works(self):
        result = check_gitignore_privacy()
        self.assertTrue(result["ok"])

    def test_docs_release_package_check_works(self):
        result = check_docs_release_package()
        self.assertTrue(result["ok"])
        self.assertEqual(result["details"]["version_value"], "v0.1.0-local")

    def test_default_safety_config_check_works(self):
        result = check_default_safety_config()
        self.assertTrue(result["ok"])

    def test_skip_tests_path_works(self):
        result = run_python_tests_check(skip=True)
        self.assertTrue(result["ok"])
        self.assertTrue(result["details"]["skipped"])

    def test_schema_constants_check_works(self):
        result = check_schema_constants()
        self.assertTrue(result["ok"])
        self.assertEqual(result["details"]["schema_version"], "1.0.0")

    def test_critical_check_can_fail(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "missing.yaml"
            result = check_default_safety_config(str(path))
            self.assertFalse(result["ok"])
            self.assertEqual(result["severity"], "critical")
