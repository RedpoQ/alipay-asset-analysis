import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from asset_analysis.preflight.checks import run_preflight


class PreflightQuotesCheckTests(unittest.TestCase):
    def _write_config(self, base: Path, holdings_path: Path, quotes_path: Path | None, strict_quotes: bool = False) -> Path:
        config = base / "config.local.yaml"
        lines = [
            "input:",
            "  mode: holdings_yaml",
            f"  holdings_yaml: {holdings_path.as_posix()}",
            "output:",
            f"  daily_dir: {(base / 'reports' / 'daily').as_posix()}",
            f"  latest_dir: {(base / 'reports' / 'private' / 'latest').as_posix()}",
            "analysis:",
            "  data_source: manual",
            "  reporter: offline",
        ]
        if quotes_path is not None:
            lines.append(f"  quotes: {quotes_path.as_posix()}")
        lines.extend(
            [
                "notification:",
                "  enabled: false",
                "  dry_run: true",
                "preflight:",
                "  enabled: true",
                f"  strict_quotes: {'true' if strict_quotes else 'false'}",
                "  fail_on_stale_quotes: false",
                "  max_normal_stale_days: 3",
                "  max_qdii_stale_days: 5",
            ]
        )
        config.write_text("\n".join(lines), encoding="utf-8")
        return config

    def _write_holdings(self, path: Path) -> None:
        path.write_text(
            'funds:\n  - code: "000001"\n    name: "QDII纳斯达克100"\n    type: "fund"\n    cost_nav: 1.0\n    amount: 100\n    target_position: 0.5\n',
            encoding="utf-8",
        )

    def test_valid_manual_quotes_pass(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            holdings = base / "holdings.yaml"
            quotes = base / "quotes.csv"
            self._write_holdings(holdings)
            quotes.write_text(
                "code,name,type,current_nav,current_price,as_of,source,currency,notes\n000001,Fund,fund,1.2,,2026-05-19,manual_nav,CNY,\n",
                encoding="utf-8",
            )
            config = self._write_config(base, holdings, quotes)
            result = run_preflight(str(config))
            self.assertTrue(result["ok"])

    def test_missing_manual_quotes_file_is_critical_when_manual(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            holdings = base / "holdings.yaml"
            self._write_holdings(holdings)
            config = self._write_config(base, holdings, base / "missing.csv")
            result = run_preflight(str(config))
            self.assertFalse(result["ok"])

    def test_missing_quote_warning_when_strict_quotes_false(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            holdings = base / "holdings.yaml"
            quotes = base / "quotes.csv"
            self._write_holdings(holdings)
            quotes.write_text(
                "code,name,type,current_nav,current_price,as_of,source,currency,notes\n999999,Other,fund,1.2,,2026-05-19,manual_nav,CNY,\n",
                encoding="utf-8",
            )
            config = self._write_config(base, holdings, quotes, strict_quotes=False)
            result = run_preflight(str(config))
            self.assertTrue(result["ok"])
            check = next(item for item in result["checks"] if item["name"] == "manual_quotes_missing_for_holdings")
            self.assertFalse(check["ok"])
            self.assertEqual(check["severity"], "warning")

    def test_missing_quote_critical_when_strict_quotes_true(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            holdings = base / "holdings.yaml"
            quotes = base / "quotes.csv"
            self._write_holdings(holdings)
            quotes.write_text(
                "code,name,type,current_nav,current_price,as_of,source,currency,notes\n999999,Other,fund,1.2,,2026-05-19,manual_nav,CNY,\n",
                encoding="utf-8",
            )
            config = self._write_config(base, holdings, quotes, strict_quotes=True)
            result = run_preflight(str(config))
            self.assertFalse(result["ok"])

    def test_stale_quote_warning(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            holdings = base / "holdings.yaml"
            quotes = base / "quotes.csv"
            self._write_holdings(holdings)
            quotes.write_text(
                "code,name,type,current_nav,current_price,as_of,source,currency,notes\n000001,Fund,fund,1.2,,2026-05-10,manual_nav,CNY,\n",
                encoding="utf-8",
            )
            config = self._write_config(base, holdings, quotes)
            result = run_preflight(str(config))
            check = next(item for item in result["checks"] if item["name"] == "manual_quotes_stale")
            self.assertFalse(check["ok"])

    def test_future_quote_warning(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            holdings = base / "holdings.yaml"
            quotes = base / "quotes.csv"
            self._write_holdings(holdings)
            future_date = (date.today() + timedelta(days=1)).isoformat()
            quotes.write_text(
                f"code,name,type,current_nav,current_price,as_of,source,currency,notes\n000001,Fund,fund,1.2,,{future_date},manual_nav,CNY,\n",
                encoding="utf-8",
            )
            config = self._write_config(base, holdings, quotes)
            result = run_preflight(str(config))
            check = next(item for item in result["checks"] if item["name"] == "manual_quotes_future_dates")
            self.assertFalse(check["ok"])

    def test_unused_quote_warning(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            holdings = base / "holdings.yaml"
            quotes = base / "quotes.csv"
            self._write_holdings(holdings)
            quotes.write_text(
                "code,name,type,current_nav,current_price,as_of,source,currency,notes\n000001,Fund,fund,1.2,,2026-05-19,manual_nav,CNY,\n888888,Unused,fund,1.1,,2026-05-19,manual_nav,CNY,\n",
                encoding="utf-8",
            )
            config = self._write_config(base, holdings, quotes)
            result = run_preflight(str(config))
            check = next(item for item in result["checks"] if item["name"] == "manual_quotes_unused_codes")
            self.assertFalse(check["ok"])
