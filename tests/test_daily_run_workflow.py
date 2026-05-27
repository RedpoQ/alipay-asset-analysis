import json
import tempfile
import unittest
from pathlib import Path

from asset_analysis.workflow.daily_run import run_daily_workflow


class DailyRunWorkflowTests(unittest.TestCase):
    def test_missing_config_returns_ok_false(self):
        result = run_daily_workflow("private/does_not_exist.local.yaml")
        self.assertFalse(result["ok"])

    def test_alipay_csv_mode_converts_and_runs_pipeline(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            private_dir = base / "private"
            private_dir.mkdir()
            reports_dir = base / "reports"
            config = base / "config.local.yaml"
            csv_path = private_dir / "alipay_holdings.local.csv"
            holdings_path = private_dir / "holdings.local.yaml"
            csv_path.write_text(
                "基金代码,基金名称,持有金额,持有份额,持仓成本价,最新净值,收益率,目标仓位\n161725,招商中证白酒指数(LOF)A,600,900,0.66,0.6732,1.96%,0.20\n",
                encoding="utf-8",
            )
            config.write_text(
                "\n".join(
                    [
                        "input:",
                        "  mode: alipay_csv",
                        f"  alipay_csv: {csv_path.as_posix()}",
                        f"  holdings_yaml: {holdings_path.as_posix()}",
                        "output:",
                        f"  daily_dir: {(reports_dir / 'daily').as_posix()}",
                        f"  latest_dir: {(reports_dir / 'private' / 'latest').as_posix()}",
                        "analysis:",
                        "  data_source: mock",
                        "  reporter: offline",
                        "  rules: examples/rules.example.yaml",
                        "  asset_groups: examples/asset_groups.example.yaml",
                        "  portfolio_template: examples/portfolio_template.example.yaml",
                        "notification:",
                        "  enabled: false",
                        "  dry_run: true",
                    ]
                ),
                encoding="utf-8",
            )
            result = run_daily_workflow(str(config))
            self.assertTrue(result["ok"])
            self.assertTrue(result["converted_holdings"])
            self.assertTrue(Path(result["report_json"]).exists())
            self.assertTrue(Path(result["report_md"]).exists())
            self.assertTrue(Path(result["run_json"]).exists())
            self.assertTrue((reports_dir / "private" / "latest" / "report.json").exists())
            self.assertIsNone(result["notification"])

    def test_holdings_yaml_mode_runs_pipeline_directly(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            private_dir = base / "private"
            private_dir.mkdir()
            reports_dir = base / "reports"
            config = base / "config.local.yaml"
            holdings_path = private_dir / "holdings.local.yaml"
            holdings_path.write_text(
                'funds:\n  - code: "161725"\n    name: "Fund"\n    type: "fund"\n    cost_nav: 1.0\n    amount: 100\n    target_position: 1.0\n',
                encoding="utf-8",
            )
            config.write_text(
                "\n".join(
                    [
                        "input:",
                        "  mode: holdings_yaml",
                        f"  holdings_yaml: {holdings_path.as_posix()}",
                        "output:",
                        f"  daily_dir: {(reports_dir / 'daily').as_posix()}",
                        f"  latest_dir: {(reports_dir / 'private' / 'latest').as_posix()}",
                        "analysis:",
                        "  data_source: mock",
                        "  reporter: offline",
                        "notification:",
                        "  enabled: false",
                    ]
                ),
                encoding="utf-8",
            )
            result = run_daily_workflow(str(config))
            self.assertTrue(result["ok"])
            self.assertIsNone(result["converted_holdings"])
            self.assertTrue(Path(result["report_json"]).exists())

    def test_notification_dry_run_can_be_invoked_when_enabled(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            private_dir = base / "private"
            private_dir.mkdir()
            reports_dir = base / "reports"
            config = base / "config.local.yaml"
            holdings_path = private_dir / "holdings.local.yaml"
            notify_config = base / "notify.yaml"
            holdings_path.write_text(
                'funds:\n  - code: "161725"\n    name: "Fund"\n    type: "fund"\n    cost_nav: 1.0\n    amount: 100\n    target_position: 1.0\n',
                encoding="utf-8",
            )
            notify_config.write_text(
                "\n".join(
                    [
                        "channels:",
                        "  - name: dry_run",
                        "    enabled: true",
                        "routing:",
                        "  default_channels:",
                        "    - dry_run",
                        "safety:",
                        "  dry_run_default: true",
                        "  allow_network_channels: false",
                    ]
                ),
                encoding="utf-8",
            )
            config.write_text(
                "\n".join(
                    [
                        "input:",
                        "  mode: holdings_yaml",
                        f"  holdings_yaml: {holdings_path.as_posix()}",
                        "output:",
                        f"  daily_dir: {(reports_dir / 'daily').as_posix()}",
                        f"  latest_dir: {(reports_dir / 'private' / 'latest').as_posix()}",
                        "analysis:",
                        "  data_source: mock",
                        "  reporter: offline",
                        "notification:",
                        "  enabled: true",
                        f"  config: {notify_config.as_posix()}",
                        "  dry_run: true",
                    ]
                ),
                encoding="utf-8",
            )
            result = run_daily_workflow(str(config))
            self.assertTrue(result["ok"])
            self.assertIsNotNone(result["notification"])
            self.assertTrue(result["notification"]["ok"])
            self.assertTrue(result["notification"]["dry_run"])

    def test_gitignore_contains_private_patterns(self):
        content = Path(".gitignore").read_text(encoding="utf-8")
        self.assertIn("private/*.csv", content)
        self.assertIn("reports/private/", content)
        self.assertIn("!private/*.example.yaml", content)

    def test_result_is_json_serializable(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            private_dir = base / "private"
            private_dir.mkdir()
            reports_dir = base / "reports"
            config = base / "config.local.yaml"
            holdings_path = private_dir / "holdings.local.yaml"
            holdings_path.write_text(
                'funds:\n  - code: "161725"\n    name: "Fund"\n    type: "fund"\n    cost_nav: 1.0\n    amount: 100\n    target_position: 1.0\n',
                encoding="utf-8",
            )
            config.write_text(
                "\n".join(
                    [
                        "input:",
                        "  mode: holdings_yaml",
                        f"  holdings_yaml: {holdings_path.as_posix()}",
                        "output:",
                        f"  daily_dir: {(reports_dir / 'daily').as_posix()}",
                        f"  latest_dir: {(reports_dir / 'private' / 'latest').as_posix()}",
                        "analysis:",
                        "  data_source: mock",
                        "  reporter: offline",
                        "notification:",
                        "  enabled: false",
                    ]
                ),
                encoding="utf-8",
            )
            result = run_daily_workflow(str(config))
            json.dumps(result, ensure_ascii=False)
