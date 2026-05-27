import tempfile
import unittest
from pathlib import Path

from asset_analysis.ux.setup_check import run_setup_check


class SetupCheckTests(unittest.TestCase):
    def test_setup_check_passes_with_valid_example_style_config(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            private_dir = base / "private"
            private_dir.mkdir()
            csv = private_dir / "alipay_holdings.local.csv"
            csv.write_text(Path("private/alipay_holdings.local.example.csv").read_text(encoding="utf-8"), encoding="utf-8")
            config = base / "config.local.yaml"
            config.write_text(
                "\n".join(
                    [
                        "profile:",
                        "  name: balanced",
                        "  file: examples/profiles/balanced.profile.yaml",
                        "input:",
                        "  mode: alipay_csv",
                        f"  alipay_csv: {csv.as_posix()}",
                        f"  holdings_yaml: {(private_dir / 'holdings.local.yaml').as_posix()}",
                        "output:",
                        f"  daily_dir: {(base / 'reports' / 'daily').as_posix()}",
                        f"  latest_dir: {(base / 'reports' / 'private' / 'latest').as_posix()}",
                        "analysis:",
                        "  data_source: mock",
                        "  reporter: offline",
                        "notification:",
                        "  enabled: false",
                        "  dry_run: true",
                    ]
                ),
                encoding="utf-8",
            )
            result = run_setup_check(str(config))
            self.assertTrue(result["ok"])

    def test_setup_check_fails_when_config_missing(self):
        result = run_setup_check("private/not_exists.local.yaml")
        self.assertFalse(result["ok"])

    def test_setup_check_warns_when_reporter_is_llm(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            private_dir = base / "private"
            private_dir.mkdir()
            holdings = private_dir / "holdings.local.yaml"
            holdings.write_text(Path("private/holdings.local.example.yaml").read_text(encoding="utf-8"), encoding="utf-8")
            config = base / "config.local.yaml"
            config.write_text(
                "\n".join(
                    [
                        "profile:",
                        "  name: balanced",
                        "  file: examples/profiles/balanced.profile.yaml",
                        "input:",
                        "  mode: holdings_yaml",
                        f"  holdings_yaml: {holdings.as_posix()}",
                        "output:",
                        f"  daily_dir: {(base / 'reports' / 'daily').as_posix()}",
                        f"  latest_dir: {(base / 'reports' / 'private' / 'latest').as_posix()}",
                        "analysis:",
                        "  data_source: mock",
                        "  reporter: llm",
                        "notification:",
                        "  enabled: false",
                        "  dry_run: true",
                    ]
                ),
                encoding="utf-8",
            )
            result = run_setup_check(str(config))
            check = next(item for item in result["checks"] if item["name"] == "reporter_offline")
            self.assertFalse(check["ok"])

    def test_setup_check_detects_missing_alipay_csv(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            config = base / "config.local.yaml"
            config.write_text(
                "\n".join(
                    [
                        "profile:",
                        "  name: balanced",
                        "  file: examples/profiles/balanced.profile.yaml",
                        "input:",
                        "  mode: alipay_csv",
                        f"  alipay_csv: {(base / 'missing.csv').as_posix()}",
                        f"  holdings_yaml: {(base / 'holdings.local.yaml').as_posix()}",
                        "output:",
                        f"  daily_dir: {(base / 'reports' / 'daily').as_posix()}",
                        f"  latest_dir: {(base / 'reports' / 'private' / 'latest').as_posix()}",
                        "analysis:",
                        "  data_source: mock",
                        "  reporter: offline",
                        "notification:",
                        "  enabled: false",
                        "  dry_run: true",
                    ]
                ),
                encoding="utf-8",
            )
            result = run_setup_check(str(config))
            self.assertFalse(result["ok"])

    def test_setup_check_detects_missing_manual_quotes_when_manual(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            private_dir = base / "private"
            private_dir.mkdir()
            holdings = private_dir / "holdings.local.yaml"
            holdings.write_text(Path("private/holdings.local.example.yaml").read_text(encoding="utf-8"), encoding="utf-8")
            config = base / "config.local.yaml"
            config.write_text(
                "\n".join(
                    [
                        "profile:",
                        "  name: balanced",
                        "  file: examples/profiles/balanced.profile.yaml",
                        "input:",
                        "  mode: holdings_yaml",
                        f"  holdings_yaml: {holdings.as_posix()}",
                        "output:",
                        f"  daily_dir: {(base / 'reports' / 'daily').as_posix()}",
                        f"  latest_dir: {(base / 'reports' / 'private' / 'latest').as_posix()}",
                        "analysis:",
                        "  data_source: manual",
                        "  reporter: offline",
                        f"  quotes: {(base / 'missing.csv').as_posix()}",
                        "notification:",
                        "  enabled: false",
                        "  dry_run: true",
                    ]
                ),
                encoding="utf-8",
            )
            result = run_setup_check(str(config))
            self.assertFalse(result["ok"])
