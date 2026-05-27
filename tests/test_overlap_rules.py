import unittest

from asset_analysis.exposure.exposure_analysis import build_exposure_analysis
from asset_analysis.exposure.overseas_classifier import load_overseas_exposure_config
from asset_analysis.models import AssetPosition


class OverlapRulesTests(unittest.TestCase):
    def setUp(self):
        self.config = load_overseas_exposure_config("examples/overseas_exposure.example.yaml")

    def test_two_nasdaq100_funds_trigger_overlap_warning(self):
        positions = [
            _position("A", "纳斯达克100A", 0.18, ["QDII", "美股", "纳斯达克100"], "satellite", "nasdaq100"),
            _position("B", "纳斯达克100B", 0.17, ["QDII", "美股", "纳斯达克100"], "satellite", "nasdaq100"),
        ]
        analysis = build_exposure_analysis(positions, self.config)
        self.assertTrue(any("纳斯达克100相关基金" in warning for warning in analysis["warnings"]))

    def test_one_nasdaq100_fund_does_not_trigger_duplicate_warning(self):
        positions = [
            _position("A", "纳斯达克100A", 0.18, ["QDII", "美股", "纳斯达克100"], "satellite", "nasdaq100"),
        ]
        analysis = build_exposure_analysis(positions, self.config)
        self.assertFalse(any("纳斯达克100相关基金" in warning for warning in analysis["warnings"]))


def _position(code: str, name: str, current_position: float, tags: list[str], role: str, overlap_key: str) -> AssetPosition:
    return AssetPosition(
        code=code,
        name=name,
        type="fund",
        cost=100.0,
        market_value=100.0 * current_position,
        profit=0.0,
        profit_rate=0.0,
        target_position=0.1,
        current_position=current_position,
        quote={"source": "mock", "error": None},
        group="overseas",
        tags=["QDII"],
        exposure_tags=tags,
        exposure_role=role,
        overlap_key=overlap_key,
    )
