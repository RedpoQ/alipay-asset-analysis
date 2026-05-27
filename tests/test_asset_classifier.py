import tempfile
import unittest
from pathlib import Path

from asset_analysis.classification.asset_classifier import classify_holding, load_asset_group_config
from asset_analysis.models import AssetHolding


class AssetClassifierTests(unittest.TestCase):
    def test_explicit_metadata_group_wins(self):
        holding = AssetHolding(code="161725", name="招商中证白酒指数(LOF)A", type="fund", amount=100, target_position=0.2, cost_nav=1.0, metadata={"group": "sector_theme", "tags": ["白酒"]})
        group, tags = classify_holding(holding, {})
        self.assertEqual(group, "sector_theme")
        self.assertEqual(tags, ["白酒"])

    def test_mapping_by_code_works(self):
        holding = AssetHolding(code="161725", name="Any", type="fund", amount=100, target_position=0.2, cost_nav=1.0)
        config = {"mappings": {"161725": {"group": "sector_theme", "tags": ["白酒"]}}, "keyword_rules": {}}
        group, tags = classify_holding(holding, config)
        self.assertEqual(group, "sector_theme")
        self.assertEqual(tags, ["白酒"])

    def test_keyword_fallback_works(self):
        holding = AssetHolding(code="X1", name="纳斯达克QDII基金", type="fund", amount=100, target_position=0.2, cost_nav=1.0)
        group, _ = classify_holding(holding, {"mappings": {}, "keyword_rules": {}})
        self.assertEqual(group, "overseas")

    def test_unknown_asset_becomes_other(self):
        holding = AssetHolding(code="X2", name="未知基金", type="fund", amount=100, target_position=0.2, cost_nav=1.0)
        group, _ = classify_holding(holding, {"mappings": {}, "keyword_rules": {}})
        self.assertEqual(group, "other")
