import tempfile
import unittest
from pathlib import Path

from asset_analysis.exposure.exposure_analysis import build_exposure_analysis
from asset_analysis.exposure.overseas_classifier import load_overseas_exposure_config
from asset_analysis.models import AssetPosition
from asset_analysis.pipeline import main as pipeline_main
from asset_analysis.workflow.daily_run import run_daily_workflow


class ExposureAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.config = load_overseas_exposure_config("examples/overseas_exposure.example.yaml")

    def test_satellite_over_max_triggers_role_warning(self):
        positions = [
            _position("A", "纳斯达克100A", 0.35, ["QDII", "美股", "纳斯达克100"], "satellite", "nasdaq100"),
        ]
        analysis = build_exposure_analysis(positions, self.config)
        self.assertTrue(any("卫星仓当前占比" in warning for warning in analysis["warnings"]))

    def test_satellite_exists_but_no_core_triggers_warning(self):
        positions = [
            _position("A", "纳斯达克100A", 0.20, ["QDII", "美股", "纳斯达克100"], "satellite", "nasdaq100"),
        ]
        analysis = build_exposure_analysis(positions, self.config)
        self.assertTrue(any("核心仓不足" in warning for warning in analysis["warnings"]))

    def test_qdii_risk_notes_appear_when_overseas_assets_exist(self):
        positions = [
            _position("A", "标普500", 0.30, ["QDII", "美股", "标普500"], "core", "sp500"),
        ]
        analysis = build_exposure_analysis(positions, self.config)
        self.assertTrue(analysis["risk_notes"])
        self.assertTrue(any("汇率波动" in note for note in analysis["risk_notes"]))

    def test_pipeline_accepts_overseas_exposure(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            holdings = base / "holdings.yaml"
            output_dir = base / "reports"
            holdings.write_text(_sample_holdings_yaml(), encoding="utf-8")
            code = pipeline_main(
                [
                    "--input",
                    str(holdings),
                    "--output",
                    str(output_dir),
                    "--data-source",
                    "mock",
                    "--reporter",
                    "offline",
                    "--asset-groups",
                    "examples/asset_groups.example.yaml",
                    "--portfolio-template",
                    "examples/portfolio_template.example.yaml",
                    "--overseas-exposure",
                    "examples/overseas_exposure.example.yaml",
                ]
            )
            self.assertEqual(code, 0)
            self.assertTrue((output_dir / "report.json").exists())

    def test_report_json_includes_exposure_analysis_when_config_is_provided(self):
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
            import json

            payload = json.loads((output_dir / "report.json").read_text(encoding="utf-8"))
            self.assertIn("exposure_analysis", payload)
            self.assertIn("overlap_groups", payload["exposure_analysis"])

    def test_daily_workflow_accepts_overseas_exposure_config(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            private_dir = base / "private"
            private_dir.mkdir()
            holdings = private_dir / "holdings.local.yaml"
            holdings.write_text(_sample_holdings_yaml(), encoding="utf-8")
            config = base / "config.local.yaml"
            config.write_text(
                "\n".join(
                    [
                        "input:",
                        "  mode: holdings_yaml",
                        f"  holdings_yaml: {holdings.as_posix()}",
                        "output:",
                        f"  daily_dir: {(base / 'reports' / 'daily').as_posix()}",
                        f"  latest_dir: {(base / 'reports' / 'private' / 'latest').as_posix()}",
                        "analysis:",
                        "  data_source: mock",
                        "  reporter: offline",
                        "  overseas_exposure: examples/overseas_exposure.example.yaml",
                        "notification:",
                        "  enabled: false",
                    ]
                ),
                encoding="utf-8",
            )
            result = run_daily_workflow(str(config))
            self.assertTrue(result["ok"])


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


def _sample_holdings_yaml() -> str:
    return '\n'.join(
        [
            'funds:',
            '  - code: "096001"',
            '    name: "标普500ETF联接(QDII)"',
            '    type: "fund"',
            '    cost_nav: 1.0',
            '    amount: 100',
            '    target_position: 0.35',
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
