import json
import unittest

from asset_analysis.holdings_parser import parse_holdings_text


class HoldingsParserTests(unittest.TestCase):
    def test_parse_yaml_holdings(self):
        yaml_text = """
funds:
  - code: "000001"
    name: "Example Fund"
    type: "fund"
    cost_nav: 1.234
    amount: 500
    target_position: 0.25
"""
        holdings = parse_holdings_text(yaml_text, suffix=".yaml")
        self.assertEqual(len(holdings), 1)
        self.assertEqual(holdings[0].code, "000001")
        self.assertEqual(holdings[0].unit_cost, 1.234)


    def test_parse_json_holdings(self):
        payload = {
            "stocks": [
                {
                    "code": "AAPL",
                    "name": "Apple",
                    "type": "stock",
                    "cost_price": 180,
                    "amount": 2,
                    "target_position": 0.20,
                }
            ]
        }
        holdings = parse_holdings_text(json.dumps(payload), suffix=".json")
        self.assertEqual(len(holdings), 1)
        self.assertEqual(holdings[0].code, "AAPL")
        self.assertEqual(holdings[0].unit_cost, 180.0)
