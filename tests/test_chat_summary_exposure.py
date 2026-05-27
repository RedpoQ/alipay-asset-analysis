import json
import tempfile
import unittest
from pathlib import Path

from asset_analysis.chat_summary.builder import build_chat_summary
from asset_analysis.pipeline import main as pipeline_main


class ChatSummaryExposureTests(unittest.TestCase):
    def test_chat_summary_includes_exposure_warnings(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            holdings = base / "holdings.yaml"
            output_dir = base / "reports"
            holdings.write_text(_sample_holdings_yaml(), encoding="utf-8")
            pipeline_main(
                [
                    "--input",
                    str(holdings),
                    "--output",
                    str(output_dir),
                    "--data-source",
                    "mock",
                    "--reporter",
                    "offline",
                    "--overseas-exposure",
                    "examples/overseas_exposure.example.yaml",
                ]
            )
            summary = build_chat_summary(str(output_dir / "report.json"))
            risk_section = next(item for item in summary["sections"] if item["title"] == "组合风险")
            joined = "\n".join(risk_section["items"])
            self.assertTrue("纳斯达克100" in joined or "卫星仓" in joined or "QDII" in joined)


def _sample_holdings_yaml() -> str:
    return '\n'.join(
        [
            'funds:',
            '  - code: "270042"',
            '    name: "纳斯达克100指数(QDII)A"',
            '    type: "fund"',
            '    cost_nav: 1.0',
            '    amount: 120',
            '    target_position: 0.2',
            '  - code: "270043"',
            '    name: "纳斯达克100指数(QDII)C"',
            '    type: "fund"',
            '    cost_nav: 1.0',
            '    amount: 130',
            '    target_position: 0.15',
        ]
    )
