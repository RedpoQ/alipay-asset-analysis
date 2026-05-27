from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from .fund_fetcher import AssetDataFetcher
from .holdings_parser import parse_holdings_file
from .classification.asset_classifier import classify_holding, load_asset_group_config
from .classification.group_analysis import build_group_analysis
from .classification.group_config import load_portfolio_template
from .exposure.exposure_analysis import build_exposure_analysis
from .exposure.overseas_classifier import classify_overseas_asset, load_overseas_exposure_config
from .models import AnalysisSummary, AssetAnalysisResult, AssetPosition
from .quotes.data_quality import build_data_quality
from .quotes.freshness import build_quote_freshness
from .reporters.registry import get_reporter
from .schema.constants import ASSET_ANALYSIS_SCHEMA_VERSION
from .schema.report_schema import build_report_run, generated_at_now
from .schema.validators import validate_report_schema
from .rules.config import load_rule_config
from .signal_engine import SignalEngine


def run_asset_pipeline(
    input_path: str | Path,
    output_dir: str | Path,
    mock_mode: bool = True,
    data_source: str | None = None,
    rules_path: str | Path | None = None,
    reporter_mode: str = "offline",
    asset_groups_path: str | Path | None = None,
    portfolio_template_path: str | Path | None = None,
    overseas_exposure_path: str | Path | None = None,
    quotes_path: str | Path | None = None,
    profile_metadata: dict[str, Any] | None = None,
    archive: bool = False,
) -> AssetAnalysisResult:
    holdings = parse_holdings_file(input_path)
    resolved_data_source = data_source or ("mock" if mock_mode else "auto")
    fetcher = AssetDataFetcher(data_source=resolved_data_source, quotes_path=str(quotes_path) if quotes_path else None)
    rule_config, rule_source = load_rule_config(rules_path)
    asset_group_config = load_asset_group_config(str(asset_groups_path) if asset_groups_path else None)
    portfolio_template = load_portfolio_template(str(portfolio_template_path) if portfolio_template_path else None)
    overseas_exposure_config = load_overseas_exposure_config(str(overseas_exposure_path) if overseas_exposure_path else None)
    generated_at = generated_at_now()
    positions: list[AssetPosition] = []

    for holding in holdings:
        quote = fetcher.fetch_asset(holding)
        group, tags = classify_holding(holding, asset_group_config)
        exposure = classify_overseas_asset(
            holding=holding,
            group=group,
            tags=tags,
            exposure_config=overseas_exposure_config,
        )
        is_qdii = bool(list(exposure.get("tags", []) or []))
        cost = round(holding.total_cost, 4)
        effective_price = quote.effective_price() or 0.0
        market_value = round(effective_price * holding.amount, 4)
        profit = round(market_value - cost, 4)
        profit_rate = round((profit / cost), 6) if cost else 0.0
        quote_payload = quote.to_dict()
        quote_payload["freshness"] = build_quote_freshness(quote_payload.get("as_of"), is_qdii=is_qdii)
        positions.append(
            AssetPosition(
                code=holding.code,
                name=holding.name,
                type=holding.type,
                cost=cost,
                market_value=market_value,
                profit=profit,
                profit_rate=profit_rate,
                target_position=holding.target_position,
                error=quote.error.__dict__ if quote.error else None,
                quote=quote_payload,
                group=group,
                tags=tags,
                exposure_tags=list(exposure.get("tags", []) or []),
                exposure_role=str(exposure.get("role", "other")),
                overlap_key=exposure.get("overlap_key"),
            )
        )

    total_cost = round(sum(item.cost for item in positions), 4)
    total_market_value = round(sum(item.market_value for item in positions), 4)
    total_profit = round(total_market_value - total_cost, 4)
    total_profit_rate = round((total_profit / total_cost), 6) if total_cost else 0.0

    for position in positions:
        position.current_position = round(
            (position.market_value / total_market_value), 6
        ) if total_market_value else 0.0

    signal_engine = SignalEngine(config=rule_config)
    signals, portfolio_warnings = signal_engine.evaluate_many(positions)
    group_analysis = build_group_analysis(positions, portfolio_template=portfolio_template)
    portfolio_warnings.extend(group_analysis.get("warnings", []))
    exposure_analysis = build_exposure_analysis(positions, overseas_exposure_config)
    portfolio_warnings.extend(exposure_analysis.get("portfolio_warnings", []))
    portfolio_warnings = _dedupe(portfolio_warnings)
    data_quality = build_data_quality(resolved_data_source, positions)
    recommendations = _build_recommendations(signals)
    summary = AnalysisSummary(
        total_cost=total_cost,
        total_market_value=total_market_value,
        total_profit=total_profit,
        total_profit_rate=total_profit_rate,
    )
    result = AssetAnalysisResult(
        schema_version=ASSET_ANALYSIS_SCHEMA_VERSION,
        generated_at=generated_at,
        run=build_report_run(
            input_path=str(input_path),
            output_dir=str(output_dir),
            data_source=resolved_data_source,
            rules_source=rule_source,
            reporter_mode=reporter_mode,
        ),
        summary=summary,
        positions=positions,
        signals=signals,
        recommendations=recommendations,
        portfolio_warnings=portfolio_warnings,
        group_analysis=group_analysis,
        exposure_analysis=exposure_analysis,
        data_quality=data_quality,
        rules={"source": rule_source, "config": rule_config.to_dict()},
        data_source=resolved_data_source,
        profile=dict(profile_metadata or {}),
    )
    reporter = get_reporter(reporter_mode)
    reporter_output = reporter.render(result)
    result.report_md = reporter_output.report_md
    result.reporter = reporter_output.to_dict()
    report_payload = result.to_dict()
    result.schema_errors = validate_report_schema(report_payload)
    report_payload = result.to_dict()
    _write_outputs(report_payload, output_dir, archive=archive)
    return result


def _build_recommendations(signals: list) -> list[str]:
    recommendations: list[str] = []
    for signal in signals:
        if signal.signal == "add":
            recommendations.append(f"Consider adding to {signal.code} in small planned increments.")
        elif signal.signal == "reduce":
            recommendations.append(f"Consider trimming {signal.code} toward its target allocation.")
    if not recommendations:
        recommendations.append("Current allocations are close to plan. Maintain holdings and monitor new data.")
    return recommendations


def _dedupe(items: list[str]) -> list[str]:
    result: list[str] = []
    for item in items:
        if item and item not in result:
            result.append(item)
    return result


def _write_outputs(report_payload: dict, output_dir: str | Path, archive: bool = False) -> None:
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    report_json_path = destination / "report.json"
    report_md_path = destination / "report.md"
    report_json_path.write_text(
        json.dumps(report_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    report_md_path.write_text(str(report_payload.get("report_md", "")), encoding="utf-8")
    run_payload = {
        "schema_version": report_payload.get("schema_version"),
        "generated_at": report_payload.get("generated_at"),
        "run": report_payload.get("run", {}),
        "report_json": str(report_json_path),
        "report_md": str(report_md_path),
        "ok": len(report_payload.get("schema_errors", [])) == 0,
        "errors": report_payload.get("schema_errors", []),
        "warnings": [],
    }
    (destination / "run.json").write_text(json.dumps(run_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    _update_latest_run(destination, run_payload)
    if archive:
        _write_archive_copy(destination, report_json_path, report_md_path)


def _update_latest_run(destination: Path, run_payload: dict) -> None:
    if "reports" not in {part.lower() for part in destination.parts}:
        return
    reports_root = destination
    while reports_root.name.lower() != "reports" and reports_root.parent != reports_root:
        reports_root = reports_root.parent
    latest_path = reports_root / "latest_run.json"
    latest_path.write_text(json.dumps(run_payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_archive_copy(destination: Path, report_json_path: Path, report_md_path: Path) -> None:
    timestamp = datetime.now().strftime("%H%M%S")
    date_part = datetime.now().strftime("%Y-%m-%d")
    reports_root = destination
    while reports_root.name.lower() != "reports" and reports_root.parent != reports_root:
        reports_root = reports_root.parent
    archive_dir = reports_root / "archive" / date_part
    archive_dir.mkdir(parents=True, exist_ok=True)
    (archive_dir / f"{timestamp}_report.json").write_text(report_json_path.read_text(encoding="utf-8"), encoding="utf-8")
    (archive_dir / f"{timestamp}_report.md").write_text(report_md_path.read_text(encoding="utf-8"), encoding="utf-8")


def _output_paths(output_dir: str | Path) -> tuple[Path, Path]:
    destination = Path(output_dir)
    return destination / "report.json", destination / "report.md"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the minimal asset analysis pipeline.")
    parser.add_argument("--input", required=True, help="Path to YAML or JSON holdings file.")
    parser.add_argument("--output", required=True, help="Directory for generated reports.")
    parser.add_argument(
        "--data-source",
        choices=("mock", "manual", "public_fund", "auto"),
        default="mock",
        help="Market data source mode. Default is deterministic offline mock data.",
    )
    parser.add_argument(
        "--reporter",
        choices=("offline", "llm", "auto"),
        default="offline",
        help="Report explanation mode. Default is offline deterministic reporting.",
    )
    parser.add_argument("--rules", help="Optional YAML rules config path.", default=None)
    parser.add_argument("--asset-groups", help="Optional asset group mapping config path.", default=None)
    parser.add_argument("--portfolio-template", help="Optional portfolio template config path.", default=None)
    parser.add_argument("--overseas-exposure", help="Optional overseas/QDII exposure config path.", default=None)
    parser.add_argument("--quotes", help="Optional manual quote CSV/YAML path.", default=None)
    parser.add_argument("--archive", action=argparse.BooleanOptionalAction, default=False, help="Also write timestamped archive copies under reports/archive.")
    parser.add_argument(
        "--mock",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Backward-compatible switch. --mock keeps using mock; --no-mock implies auto when --data-source is not set explicitly.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        explicit_data_source = None
        if argv is not None and "--data-source" in argv:
            explicit_data_source = args.data_source
        elif "--data-source" in sys.argv[1:]:
            explicit_data_source = args.data_source
        run_asset_pipeline(
            input_path=args.input,
            output_dir=args.output,
            mock_mode=args.mock,
            data_source=explicit_data_source,
            rules_path=args.rules,
            reporter_mode=args.reporter,
            asset_groups_path=args.asset_groups,
            portfolio_template_path=args.portfolio_template,
            overseas_exposure_path=args.overseas_exposure,
            quotes_path=args.quotes,
            archive=args.archive,
        )
    except Exception as exc:
        print(f"Asset analysis failed: {exc}", file=sys.stderr)
        return 1

    report_json, report_md = _output_paths(args.output)
    print(f"Generated JSON report: {report_json}")
    print(f"Generated Markdown report: {report_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
