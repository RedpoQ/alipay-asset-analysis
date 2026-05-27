from __future__ import annotations

from pathlib import Path


def render_config_template(profile: str = "balanced", data_source: str = "mock") -> str:
    profile = (profile or "balanced").strip() or "balanced"
    data_source = (data_source or "mock").strip() or "mock"
    profile_file = f"examples/profiles/{profile}.profile.yaml"
    return "\n".join(
        [
            "profile:",
            f"  name: {profile}",
            f"  file: {profile_file}",
            "",
            "input:",
            "  mode: alipay_csv",
            "  alipay_csv: private/alipay_holdings.local.csv",
            "  holdings_yaml: private/holdings.local.yaml",
            "",
            "output:",
            "  daily_dir: reports/daily",
            "  latest_dir: reports/private/latest",
            "",
            "analysis:",
            f"  data_source: {data_source}",
            "  reporter: offline",
            "  rules: examples/rules.example.yaml",
            "  asset_groups: examples/asset_groups.example.yaml",
            "  portfolio_template: examples/portfolio_template.example.yaml",
            "  overseas_exposure: examples/overseas_exposure.example.yaml",
            "  quotes: private/manual_quotes.local.csv",
            "",
            "notification:",
            "  enabled: false",
            "  config: examples/notify.example.yaml",
            "  dry_run: true",
            "",
            "history:",
            "  enabled: true",
            "  reports_dir: reports/daily",
            "  index_path: reports/history_index.json",
            "  trend_output_dir: reports/trend",
            "",
            "chat_summary:",
            "  enabled: true",
            "  style: wechat",
            "  max_signals: 3",
            "  max_warnings: 5",
            "",
            "preflight:",
            "  enabled: true",
            "  strict_quotes: false",
            "  fail_on_stale_quotes: false",
            "  fail_on_duplicate_codes: false",
            "  max_normal_stale_days: 3",
            "  max_qdii_stale_days: 5",
            "",
        ]
    )


def choose_existing_template(*paths: str | Path) -> Path | None:
    for item in paths:
        path = Path(item)
        if path.exists():
            return path
    return None
