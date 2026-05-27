import tempfile
import unittest
from pathlib import Path

from asset_analysis.ux.setup_check import run_setup_check


class SetupRepairHintsTests(unittest.TestCase):
    def test_missing_config_includes_init_hint(self):
        result = run_setup_check("private/not_exists.local.yaml")
        self.assertTrue(any(item["problem"] == "missing_config" for item in result["repair_hints"]))

    def test_missing_manual_quotes_includes_copy_hint(self):
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
            self.assertTrue(any(item["problem"] == "missing_manual_quotes" for item in result["repair_hints"]))

    def test_unknown_alipay_headers_include_preview_hint(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            private_dir = base / "private"
            private_dir.mkdir()
            csv_path = private_dir / "alipay_holdings.local.csv"
            csv_path.write_text("奇怪字段,另一个字段\n1,2\n", encoding="utf-8")
            config = base / "config.local.yaml"
            config.write_text(
                "\n".join(
                    [
                        "profile:",
                        "  name: balanced",
                        "  file: examples/profiles/balanced.profile.yaml",
                        "input:",
                        "  mode: alipay_csv",
                        f"  alipay_csv: {csv_path.as_posix()}",
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
            self.assertTrue(any(item["problem"] == "unknown_csv_headers" for item in result["repair_hints"]))


if __name__ == "__main__":
    unittest.main()
