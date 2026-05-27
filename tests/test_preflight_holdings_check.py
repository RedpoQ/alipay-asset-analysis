import tempfile
import unittest
from pathlib import Path

from asset_analysis.preflight.checks import run_preflight


class PreflightHoldingsCheckTests(unittest.TestCase):
    def _write_base_config(self, base: Path, holdings_path: Path, extra: list[str] | None = None) -> Path:
        config = base / "config.local.yaml"
        lines = [
            "input:",
            "  mode: holdings_yaml",
            f"  holdings_yaml: {holdings_path.as_posix()}",
            "output:",
            f"  daily_dir: {(base / 'reports' / 'daily').as_posix()}",
            f"  latest_dir: {(base / 'reports' / 'private' / 'latest').as_posix()}",
            "analysis:",
            "  data_source: mock",
            "  reporter: offline",
            "notification:",
            "  enabled: false",
            "  dry_run: true",
            "preflight:",
            "  enabled: true",
        ]
        if extra:
            lines.extend(extra)
        config.write_text("\n".join(lines), encoding="utf-8")
        return config

    def test_valid_holdings_passes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            holdings = base / "holdings.yaml"
            holdings.write_text(
                'funds:\n  - code: "000001"\n    name: "Fund"\n    type: "fund"\n    cost_nav: 1.0\n    amount: 100\n    target_position: 0.5\n',
                encoding="utf-8",
            )
            config = self._write_base_config(base, holdings)
            result = run_preflight(str(config))
            self.assertTrue(result["ok"])

    def test_missing_holdings_file_is_critical(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            holdings = base / "missing.yaml"
            config = self._write_base_config(base, holdings)
            result = run_preflight(str(config))
            self.assertFalse(result["ok"])
            self.assertTrue(any(item["name"] == "holdings_file_exists" and item["severity"] == "critical" for item in result["checks"]))

    def test_invalid_numeric_amount_is_critical(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            holdings = base / "holdings.yaml"
            holdings.write_text(
                'funds:\n  - code: "000001"\n    name: "Fund"\n    type: "fund"\n    cost_nav: 1.0\n    amount: -100\n    target_position: 0.5\n',
                encoding="utf-8",
            )
            config = self._write_base_config(base, holdings)
            result = run_preflight(str(config))
            self.assertFalse(result["ok"])
            check = next(item for item in result["checks"] if item["name"] == "holdings_numeric_values")
            self.assertFalse(check["ok"])

    def test_duplicate_holding_code_warning(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            holdings = base / "holdings.yaml"
            holdings.write_text(
                'funds:\n  - code: "000001"\n    name: "Fund A"\n    type: "fund"\n    cost_nav: 1.0\n    amount: 100\n    target_position: 0.2\n  - code: "000001"\n    name: "Fund B"\n    type: "fund"\n    cost_nav: 1.1\n    amount: 100\n    target_position: 0.3\n',
                encoding="utf-8",
            )
            config = self._write_base_config(base, holdings)
            result = run_preflight(str(config))
            self.assertTrue(result["ok"])
            check = next(item for item in result["checks"] if item["name"] == "holdings_duplicate_codes")
            self.assertFalse(check["ok"])
            self.assertEqual(check["severity"], "warning")
