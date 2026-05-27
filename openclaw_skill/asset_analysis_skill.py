from __future__ import annotations

from asset_analysis.openclaw_adapter import run_asset_analysis_skill


def run(args: dict | None = None) -> dict:
    payload = dict(args or {})
    return run_asset_analysis_skill(
        holdings_path=str(payload.get("holdings_path", "")),
        output_dir=str(payload.get("output_dir", "")),
        data_source=str(payload.get("data_source", "mock")),
        rules_path=payload.get("rules_path"),
        reporter=str(payload.get("reporter", "offline")),
        alipay_input_path=payload.get("alipay_input_path"),
        alipay_output_path=payload.get("alipay_output_path"),
        alipay_output_format=str(payload.get("alipay_output_format", "yaml")),
    )
