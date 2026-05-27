from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from ..alipay.preview import build_preview_payload
from ..holdings_parser import _load_yaml_like
from ..onboarding.repair_hints import build_repair_hints
from ..profiles.resolver import resolve_profile_config
from ..schema.constants import ASSET_ANALYSIS_SCHEMA_VERSION
from ..schema.errors import make_error
from ..workflow.config import load_workflow_config_bundle


def run_setup_check(config_path: str = "private/config.local.yaml", markdown_output: str | None = None) -> dict[str, Any]:
    path = Path(config_path)
    checks: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    warnings: list[str] = []

    checks.append(_check("config_exists", path.exists(), "critical", f"配置文件存在：{config_path}" if path.exists() else f"配置文件不存在：{config_path}", {"path": config_path}))
    if not path.exists():
        payload = _payload(False, checks, [make_error("setup", "CONFIG_NOT_FOUND", f"Config not found: {config_path}")], [], config_path=config_path)
        _write_markdown_if_needed(payload, markdown_output)
        return payload

    try:
        raw = _load_yaml_like(path.read_text(encoding="utf-8"))
        profile_result = resolve_profile_config(raw)
        if profile_result.get("errors"):
            for item in profile_result.get("errors", []):
                errors.append(item)
            checks.append(_check("profile_resolves", False, "critical", "Profile resolution failed.", {"errors": profile_result.get("errors", [])}))
            payload = _payload(False, checks, errors, warnings, config_path=config_path)
            _write_markdown_if_needed(payload, markdown_output)
            return payload
        bundle = load_workflow_config_bundle(config_path)
        config = bundle.config
        effective = bundle.effective_config
        warnings.extend(bundle.warnings)
        checks.append(_check("profile_resolves", True, "critical", "Profile resolves successfully.", {"profile": profile_result.get("profile", {})}))
    except Exception as exc:
        payload = _payload(False, checks, [make_error("setup", "CONFIG_ERROR", str(exc))], warnings, config_path=config_path)
        _write_markdown_if_needed(payload, markdown_output)
        return payload

    private_dir = Path("private")
    latest_dir = Path(str((effective.get("output", {}) or {}).get("latest_dir", "reports/private/latest")))
    checks.append(_check("private_dir_exists", private_dir.exists(), "warning", "private 目录存在。" if private_dir.exists() else "private 目录不存在。", {"path": str(private_dir)}))
    _ensure_dir_check(checks, "latest_dir_writable", latest_dir)

    input_mode = str((effective.get("input", {}) or {}).get("mode", ""))
    alipay_csv = Path(str((effective.get("input", {}) or {}).get("alipay_csv", "")))
    holdings_yaml = Path(str((effective.get("input", {}) or {}).get("holdings_yaml", "")))
    if input_mode == "alipay_csv":
        checks.append(_check("alipay_csv_exists", alipay_csv.exists(), "critical", f"Alipay CSV 存在：{alipay_csv}" if alipay_csv.exists() else f"Alipay CSV 不存在：{alipay_csv}", {"path": str(alipay_csv)}))
        if alipay_csv.exists():
            preview = build_preview_payload(alipay_csv)
            mapped_fields = set((preview.get("canonical_field_mapping", {}) or {}).keys())
            missing_headers = sorted(field for field in ("code", "name") if field not in mapped_fields)
            if not ({"market_value", "amount"} & mapped_fields):
                missing_headers.append("market_value")
            checks.append(
                _check(
                    "alipay_csv_headers_known",
                    not missing_headers,
                    "critical",
                    "Alipay CSV headers map to required canonical fields."
                    if not missing_headers
                    else f"Alipay CSV headers are missing required mappings: {', '.join(missing_headers)}",
                    {
                        "path": str(alipay_csv),
                        "missing_fields": missing_headers,
                        "mapping": preview.get("canonical_field_mapping", {}),
                        "unknown_columns": preview.get("unknown_columns", []),
                    },
                )
            )
    if input_mode == "holdings_yaml":
        checks.append(_check("holdings_yaml_exists", holdings_yaml.exists(), "critical", f"Holdings YAML 存在：{holdings_yaml}" if holdings_yaml.exists() else f"Holdings YAML 不存在：{holdings_yaml}", {"path": str(holdings_yaml)}))

    analysis = effective.get("analysis", {}) or {}
    data_source = str(analysis.get("data_source", "unknown"))
    quotes_path = analysis.get("quotes")
    if data_source == "manual":
        quote_file = Path(str(quotes_path or ""))
        checks.append(_check("manual_quotes_exists", quote_file.exists(), "critical", f"Manual quotes 文件存在：{quote_file}" if quote_file.exists() else f"Manual quotes 文件不存在：{quote_file}", {"path": str(quote_file)}))
    _check_file_reference(checks, "profile_file_exists", (effective.get("profile", {}) or {}).get("file"), "critical")
    _check_file_reference(checks, "rules_file_exists", analysis.get("rules"), "critical")
    _check_file_reference(checks, "asset_groups_file_exists", analysis.get("asset_groups"), "warning")
    _check_file_reference(checks, "portfolio_template_file_exists", analysis.get("portfolio_template"), "warning")
    _check_file_reference(checks, "overseas_exposure_file_exists", analysis.get("overseas_exposure"), "warning")
    notification = effective.get("notification", {}) or {}
    if notification.get("enabled"):
        _check_file_reference(checks, "notification_config_exists", notification.get("config"), "warning")
    checks.append(_check("notification_safe_default", not ((effective.get("notification", {}) or {}).get("enabled") and not (effective.get("notification", {}) or {}).get("dry_run", True)), "warning", "通知保持关闭或 dry_run。" if not ((effective.get("notification", {}) or {}).get("enabled") and not (effective.get("notification", {}) or {}).get("dry_run", True)) else "通知已启用真实发送，请再次确认。"))
    reporter = str(analysis.get("reporter", "offline"))
    checks.append(_check("reporter_offline", reporter == "offline", "warning", "Reporter 默认使用 offline。" if reporter == "offline" else "当前 reporter 不是 offline，请确认这是你的预期。", {"reporter": reporter}))
    checks.append(_check("data_source_status", data_source != "unknown", "info", f"当前数据源：{data_source}", {"data_source": data_source}))

    for item in checks:
        if item["ok"]:
            continue
        if item["severity"] == "critical":
            errors.append(make_error("setup", f"SETUP_{item['name'].upper()}", item["message"], dict(item.get("details", {}))))
        elif item["severity"] == "warning":
            warnings.append(item["message"])

    payload = _payload(
        len([item for item in checks if not item["ok"] and item["severity"] == "critical"]) == 0,
        checks,
        errors,
        warnings,
        config_path=config_path,
        data_source=data_source,
    )
    _write_markdown_if_needed(payload, markdown_output)
    return payload


def _ensure_dir_check(checks: list[dict[str, Any]], name: str, path: Path) -> None:
    try:
        path.mkdir(parents=True, exist_ok=True)
        checks.append(_check(name, True, "critical", f"输出目录可创建：{path}", {"path": str(path)}))
    except Exception as exc:
        checks.append(_check(name, False, "critical", f"输出目录不可创建：{path}", {"path": str(path), "error": str(exc)}))


def _check_file_reference(checks: list[dict[str, Any]], name: str, raw_path: Any, severity: str) -> None:
    if raw_path in (None, ""):
        return
    path = Path(str(raw_path))
    checks.append(
        _check(
            "config_file_reference_missing" if not path.exists() else name,
            path.exists(),
            severity,
            f"配置引用文件存在：{path}" if path.exists() else f"配置引用文件不存在：{path}",
            {"path": str(path), "reference": name},
        )
    )


def _payload(
    ok: bool,
    checks: list[dict[str, Any]],
    errors: list[dict[str, Any]],
    warnings: list[str],
    *,
    config_path: str,
    data_source: str | None = None,
) -> dict[str, Any]:
    repair_hints = build_repair_hints(checks, config_path=config_path, data_source=data_source)
    return {
        "schema_version": ASSET_ANALYSIS_SCHEMA_VERSION,
        "ok": ok and not errors,
        "generated_at": datetime.now().astimezone().isoformat(),
        "checks": checks,
        "summary": {
            "total": len(checks),
            "passed": len([item for item in checks if item.get("ok")]),
            "failed": len([item for item in checks if not item.get("ok")]),
            "warnings": len([item for item in checks if not item.get("ok") and item.get("severity") == "warning"]),
            "critical_failed": len([item for item in checks if not item.get("ok") and item.get("severity") == "critical"]),
        },
        "errors": errors,
        "warnings": warnings,
        "repair_hints": repair_hints,
    }


def _check(name: str, ok: bool, severity: str, message: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"name": name, "ok": ok, "severity": severity, "message": message, "details": details or {}}


def _write_markdown_if_needed(payload: dict[str, Any], markdown_output: str | None) -> None:
    if not markdown_output:
        return
    path = Path(markdown_output)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Setup Check",
        f"- Status: {'PASS' if payload.get('ok') else 'BLOCKED'}",
        f"- Total Checks: {payload.get('summary', {}).get('total', 0)}",
        f"- Critical Failed: {payload.get('summary', {}).get('critical_failed', 0)}",
        "",
        "## Checks",
    ]
    for item in payload.get("checks", []):
        lines.append(f"- [{item.get('severity')}] {item.get('name')}: {item.get('message')}")
    repair_hints = payload.get("repair_hints", []) or []
    if repair_hints:
        lines.extend(["", "## Repair Hints"])
        for item in repair_hints:
            lines.append(f"- {item.get('problem')}: {item.get('suggestion')}")
    path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a simple local setup check for the single-channel Alipay workflow.")
    parser.add_argument("--config", default="private/config.local.yaml", help="Path to local workflow config.")
    parser.add_argument("--markdown", help="Optional markdown output path.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    result = run_setup_check(config_path=args.config, markdown_output=args.markdown)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
