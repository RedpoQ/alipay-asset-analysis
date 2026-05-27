import unittest

from asset_analysis.models import AssetPosition
from asset_analysis.rules.config import RuleConfig
from asset_analysis.signal_engine import SignalEngine


class SignalEngineTests(unittest.TestCase):
    def test_signal_engine_returns_add(self):
        engine = SignalEngine(RuleConfig())
        position = AssetPosition(
            code="000001",
            name="Example Fund",
            type="fund",
            cost=1000,
            market_value=900,
            profit=-100,
            profit_rate=-0.10,
            target_position=0.30,
            current_position=0.20,
        )
        self.assertEqual(engine.evaluate(position).signal, "add")

    def test_signal_engine_returns_reduce(self):
        engine = SignalEngine()
        position = AssetPosition(
            code="510300",
            name="ETF",
            type="etf",
            cost=1000,
            market_value=1100,
            profit=100,
            profit_rate=0.10,
            target_position=0.20,
            current_position=0.30,
        )
        self.assertEqual(engine.evaluate(position).signal, "reduce")

    def test_signal_engine_returns_hold_for_large_loss(self):
        engine = SignalEngine()
        position = AssetPosition(
            code="LOSS",
            name="Loss Asset",
            type="stock",
            cost=1000,
            market_value=700,
            profit=-300,
            profit_rate=-0.30,
            target_position=0.40,
            current_position=0.20,
        )
        self.assertEqual(engine.evaluate(position).signal, "hold")
