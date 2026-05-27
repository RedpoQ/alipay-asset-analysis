import tempfile
import unittest
from pathlib import Path

from asset_analysis.models import AssetHolding
from asset_analysis.quotes.manual_quote_source import ManualQuoteDataSource
from asset_analysis.quotes.quote_loader import load_manual_quotes


class ManualQuoteSourceTests(unittest.TestCase):
    def test_manual_quote_csv_loads(self):
        records = load_manual_quotes("examples/manual_quotes.example.csv")
        self.assertIn("000001", records)

    def test_manual_quote_yaml_loads(self):
        records = load_manual_quotes("examples/manual_quotes.example.yaml")
        self.assertIn("110022", records)

    def test_manual_source_matches_holding_by_code(self):
        source = ManualQuoteDataSource("examples/manual_quotes.example.csv")
        quote = source.fetch_quote(_holding("000001", "华夏成长混合"))
        self.assertEqual(quote.current_nav, 1.234)
        self.assertEqual(quote.source, "manual_nav")

    def test_missing_quote_returns_structured_quote_error(self):
        source = ManualQuoteDataSource("examples/manual_quotes.example.csv")
        quote = source.fetch_quote(_holding("999999", "未知基金"))
        self.assertIsNotNone(quote.error)
        self.assertEqual(quote.error.code, "MANUAL_QUOTE_MISSING")


def _holding(code: str, name: str) -> AssetHolding:
    return AssetHolding(code=code, name=name, type="fund", amount=100, target_position=0.2, cost_nav=1.0)
