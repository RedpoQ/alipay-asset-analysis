import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from asset_analysis.hermes.cronjob_runner import main as hermes_cronjob_main, run_hermes_daily_job


class HermesCronjobRunnerTests(unittest.TestCase):
    def _write_config(self, base: Path, *, chat_summary_enabled: bool = True) -> Path:
        private_dir = base / "private"
        private_dir.mkdir(parents=True, exist_ok=True)
        reports_dir = base / "reports"
        holdings_path = private_dir / "holdings.local.yaml"
        holdings_path.write_text(Path("private/holdings.local.example.yaml").read_text(encoding="utf-8"), encoding="utf-8")
        config_path = base / "config.local.yaml"
        config_path.write_text(
            "\n".join(
                [
                    "profile:",
                    "  name: balanced",
                    "  file: examples/profiles/balanced.profile.yaml",
                    "input:",
                    "  mode: holdings_yaml",
                    f"  holdings_yaml: {holdings_path.as_posix()}",
                    "output:",
                    f"  daily_dir: {(reports_dir / 'daily').as_posix()}",
                    f"  latest_dir: {(reports_dir / 'private' / 'latest').as_posix()}",
                    "analysis:",
                    "  data_source: mock",
                    "  reporter: offline",
                    "notification:",
                    "  enabled: false",
                    "  dry_run: true",
                    "chat_summary:",
                    f"  enabled: {'true' if chat_summary_enabled else 'false'}",
                    "  style: wechat",
                    "  max_signals: 3",
                    "  max_warnings: 5",
                    "preflight:",
                    "  enabled: true",
                ]
            ),
            encoding="utf-8",
        )
        return config_path

    def test_cronjob_runner_succeeds_when_daily_workflow_succeeds(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            config_path = self._write_config(base)
            latest_dir = base / "reports" / "private" / "latest"
            result = run_hermes_daily_job(config_path=str(config_path), latest_dir=str(latest_dir))
            self.assertTrue(result["ok"])
            self.assertTrue(result["chat_summary"])
            self.assertTrue(result["chat_summary_path"].endswith("chat_summary.txt"))

    def test_cronjob_runner_reads_chat_summary(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            config_path = self._write_config(base)
            latest_dir = base / "reports" / "private" / "latest"
            result = run_hermes_daily_job(config_path=str(config_path), latest_dir=str(latest_dir))
            file_text = (latest_dir / "chat_summary.txt").read_text(encoding="utf-8").strip()
            self.assertEqual(result["chat_summary"], file_text)

    def test_summary_only_output_can_be_produced(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            config_path = self._write_config(base)
            latest_dir = base / "reports" / "private" / "latest"
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = hermes_cronjob_main(
                    ["--config", str(config_path), "--latest-dir", str(latest_dir), "--summary-only"]
                )
            self.assertEqual(exit_code, 0)
            self.assertIn("规则驱动", buffer.getvalue())

    def test_missing_chat_summary_returns_structured_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            config_path = self._write_config(base, chat_summary_enabled=False)
            latest_dir = base / "reports" / "private" / "latest"
            result = run_hermes_daily_job(config_path=str(config_path), latest_dir=str(latest_dir))
            self.assertFalse(result["ok"])
            self.assertEqual(result["errors"][0]["stage"], "read_summary")

    def test_missing_config_returns_structured_error(self):
        result = run_hermes_daily_job(config_path="private/not_exists.local.yaml", latest_dir="reports/private/latest")
        self.assertFalse(result["ok"])
        self.assertEqual(result["errors"][0]["stage"], "setup")

    def test_json_only_output_can_be_produced(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            config_path = self._write_config(base)
            latest_dir = base / "reports" / "private" / "latest"
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = hermes_cronjob_main(["--config", str(config_path), "--latest-dir", str(latest_dir), "--json-only"])
            self.assertEqual(exit_code, 0)
            payload = json.loads(buffer.getvalue())
            self.assertTrue(payload["ok"])


if __name__ == "__main__":
    unittest.main()
