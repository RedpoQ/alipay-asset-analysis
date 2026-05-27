import unittest

from asset_analysis.exposure.overseas_classifier import classify_overseas_asset, load_overseas_exposure_config
from asset_analysis.localization.group_copy import localize_group_name
from asset_analysis.models import AssetHolding


class OverseasClassifierTests(unittest.TestCase):
    def setUp(self):
        self.config = load_overseas_exposure_config("examples/overseas_exposure.example.yaml")

    def test_sp500_fund_name_classified_as_sp500_core(self):
        holding = AssetHolding(code="096001", name="标普500ETF联接(QDII)", type="fund", amount=100, target_position=0.3, cost_nav=1.0)
        result = classify_overseas_asset(holding=holding, group="overseas", tags=["QDII"], exposure_config=self.config)
        self.assertEqual(result["overlap_key"], "sp500")
        self.assertEqual(result["role"], "core")

    def test_nasdaq100_fund_name_classified_as_nasdaq100_satellite(self):
        holding = AssetHolding(code="270042", name="纳斯达克100指数(QDII)", type="fund", amount=100, target_position=0.2, cost_nav=1.0)
        result = classify_overseas_asset(holding=holding, group="overseas", tags=["QDII"], exposure_config=self.config)
        self.assertEqual(result["overlap_key"], "nasdaq100")
        self.assertEqual(result["role"], "satellite")

    def test_qdii_keyword_creates_overseas_tags(self):
        holding = AssetHolding(code="501300", name="全球精选QDII", type="fund", amount=100, target_position=0.1, cost_nav=1.0)
        result = classify_overseas_asset(holding=holding, group="other", tags=[], exposure_config=self.config)
        self.assertIn("QDII", result["tags"])
        self.assertIn("海外资产", result["tags"])

    def test_localization_maps_exposure_role_names(self):
        self.assertEqual(localize_group_name("core"), "核心仓")
        self.assertEqual(localize_group_name("satellite"), "卫星仓")
        self.assertEqual(localize_group_name("sp500"), "标普500")
