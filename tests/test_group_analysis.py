import unittest

from asset_analysis.classification.group_analysis import build_group_analysis
from asset_analysis.classification.group_config import GroupRuleConfig, GroupTargetConfig, PortfolioTemplate
from asset_analysis.models import AssetPosition


class GroupAnalysisTests(unittest.TestCase):
    def test_group_analysis_calculates_current_position(self):
        positions = [
            AssetPosition(code="A", name="A", type="fund", cost=100, market_value=100, profit=0, profit_rate=0, target_position=0.5, current_position=0.5, group="sector_theme", tags=["消费"]),
            AssetPosition(code="B", name="B", type="fund", cost=100, market_value=300, profit=0, profit_rate=0, target_position=0.5, current_position=0.5, group="active_equity", tags=["消费"]),
        ]
        result = build_group_analysis(positions)
        self.assertEqual(result["groups"][0]["current_position"], 0.75)

    def test_group_over_max_creates_warning(self):
        positions = [
            AssetPosition(code="A", name="A", type="fund", cost=100, market_value=300, profit=0, profit_rate=0, target_position=0.5, current_position=0.75, group="sector_theme", tags=["消费"]),
            AssetPosition(code="B", name="B", type="fund", cost=100, market_value=100, profit=0, profit_rate=0, target_position=0.5, current_position=0.25, group="bond", tags=["债券"]),
        ]
        template = PortfolioTemplate(groups={"sector_theme": GroupTargetConfig(target_position=0.2, max_position=0.3)})
        result = build_group_analysis(positions, portfolio_template=template)
        self.assertTrue(result["warnings"])

    def test_group_under_target_creates_warning(self):
        positions = [
            AssetPosition(code="A", name="A", type="fund", cost=100, market_value=100, profit=0, profit_rate=0, target_position=0.5, current_position=0.25, group="bond", tags=["债券"]),
            AssetPosition(code="B", name="B", type="fund", cost=100, market_value=300, profit=0, profit_rate=0, target_position=0.5, current_position=0.75, group="sector_theme", tags=["消费"]),
        ]
        template = PortfolioTemplate(groups={"bond": GroupTargetConfig(target_position=0.4, max_position=0.5)})
        result = build_group_analysis(positions, portfolio_template=template)
        self.assertTrue(any("below target_position" in item for item in result["warnings"]))

    def test_tag_concentration_warning_works(self):
        positions = [
            AssetPosition(code="A", name="A", type="fund", cost=100, market_value=300, profit=0, profit_rate=0, target_position=0.5, current_position=0.75, group="sector_theme", tags=["消费"]),
            AssetPosition(code="B", name="B", type="fund", cost=100, market_value=100, profit=0, profit_rate=0, target_position=0.5, current_position=0.25, group="active_equity", tags=["消费"]),
        ]
        template = PortfolioTemplate(rules=GroupRuleConfig(warn_when_single_tag_concentration_over=0.3))
        result = build_group_analysis(positions, portfolio_template=template)
        self.assertTrue(any(item["warnings"] for item in result["tag_concentration"]))
