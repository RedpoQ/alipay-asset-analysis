import unittest
from datetime import date

from asset_analysis.quotes.freshness import build_quote_freshness


class QuoteFreshnessTests(unittest.TestCase):
    def test_stale_quote_detected(self):
        freshness = build_quote_freshness("2026-05-10", is_qdii=False, today=date(2026, 5, 18))
        self.assertEqual(freshness["status"], "stale")

    def test_qdii_threshold_allows_longer_delay(self):
        freshness = build_quote_freshness("2026-05-14", is_qdii=True, today=date(2026, 5, 18))
        self.assertEqual(freshness["status"], "fresh")

    def test_future_as_of_warning_works(self):
        freshness = build_quote_freshness("2026-05-20", is_qdii=False, today=date(2026, 5, 18))
        self.assertEqual(freshness["status"], "future_date")

    def test_missing_as_of_is_warning(self):
        freshness = build_quote_freshness(None, is_qdii=False, today=date(2026, 5, 18))
        self.assertEqual(freshness["status"], "missing_date")
