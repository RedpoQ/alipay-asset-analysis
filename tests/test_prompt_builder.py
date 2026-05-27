import unittest

from asset_analysis.models import AnalysisSummary, AssetAnalysisResult, AssetPosition, SignalResult
from asset_analysis.reporters.prompt_builder import build_report_prompt


class PromptBuilderTests(unittest.TestCase):
    def test_prompt_builder_includes_signals_and_portfolio_warnings(self):
        result = AssetAnalysisResult(
            summary=AnalysisSummary(1, 1, 0, 0),
            positions=[AssetPosition(code="A", name="Asset", type="fund", cost=1, market_value=1, profit=0, profit_rate=0, target_position=0.5)],
            signals=[SignalResult(code="A", signal="hold", reason="Hold for now", name="Asset", type="fund")],
            portfolio_warnings=["Too concentrated"],
            rules={"source": "default", "config": {}},
            data_source="mock",
        )
        prompt = build_report_prompt(result)
        self.assertIn('"signals"', prompt)
        self.assertIn('"portfolio_warnings"', prompt)
        self.assertIn("Too concentrated", prompt)

    def test_prompt_builder_includes_no_prediction_instruction(self):
        result = AssetAnalysisResult(
            summary=AnalysisSummary(1, 1, 0, 0),
            positions=[],
            signals=[],
            rules={"source": "default", "config": {}},
            data_source="mock",
        )
        prompt = build_report_prompt(result)
        self.assertIn("不要预测未来价格", prompt)
        self.assertIn("不要修改 add/reduce/hold 信号", prompt)
