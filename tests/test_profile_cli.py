import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from asset_analysis.profiles.cli import main


class ProfileCliTests(unittest.TestCase):
    def test_cli_list_works(self):
        sink = io.StringIO()
        with redirect_stdout(sink):
            result = main(["--list"])
        output = sink.getvalue()
        self.assertEqual(result, 0)
        self.assertIn("balanced", output)
        self.assertIn("growth", output)

    def test_cli_resolves_balanced_profile(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "resolved.json"
            sink = io.StringIO()
            with redirect_stdout(sink):
                result = main(["--profile", "examples/profiles/balanced.profile.yaml", "--output", str(output)])
            self.assertEqual(result, 0)
            self.assertTrue(output.exists())
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["profile"]["name"], "balanced")
