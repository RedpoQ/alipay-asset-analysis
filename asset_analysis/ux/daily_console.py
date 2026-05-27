from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def format_daily_console_output(result: dict[str, Any]) -> str:
    status = "PASS" if result.get("ok") else "BLOCKED"
    profile = result.get("profile", {}) or {}
    preflight = result.get("preflight", {}) or {}
    profile_name = str(profile.get("name", "unknown"))
    display_name = str(profile.get("display_name", "")).strip()
    preflight_summary = _format_preflight_summary(preflight)
    latest_dir = Path(str(result.get("latest_dir") or "")).resolve() if result.get("latest_dir") else None
    report_path = latest_dir / "report.md" if latest_dir else None
    chat_path = latest_dir / "chat_summary.txt" if latest_dir else None
    preflight_path = latest_dir / "preflight_report.md" if latest_dir else None
    one_line = _load_chat_summary_one_line(result)
    warnings = result.get("warnings", []) or []
    main_warning = str(warnings[0]) if warnings else "暂无明显额外提醒。"
    data_source = _read_effective_data_source(result)
    lines = [
        f"Daily Asset Analysis: {status}",
        "",
        f"Profile: {profile_name}" + (f" / {display_name}" if display_name else ""),
        f"Data source: {data_source}",
        f"Preflight: {preflight_summary}",
        "",
        "Summary:",
        one_line,
        "",
        "Main warning:",
        main_warning,
        "",
        "Outputs:",
    ]
    if report_path:
        lines.append(f"- Report: {report_path}")
    if chat_path:
        lines.append(f"- Chat summary: {chat_path}")
    if preflight_path and preflight_path.exists():
        lines.append(f"- Preflight: {preflight_path}")
    lines.extend(
        [
            "",
            "Next:",
            "Open chat_summary.txt and paste it into Hermes/WeChat if needed.",
        ]
    )
    return "\n".join(lines).strip() + "\n"


def _format_preflight_summary(preflight: dict[str, Any]) -> str:
    if not preflight:
        return "not enabled"
    warnings = int((preflight.get("summary", {}) or {}).get("warnings", 0))
    if preflight.get("ok"):
        return "PASS" if warnings == 0 else f"PASS with {warnings} warnings"
    return "BLOCKED"


def _load_chat_summary_one_line(result: dict[str, Any]) -> str:
    latest_dir = result.get("latest_dir")
    if latest_dir:
        chat_json = Path(str(latest_dir)) / "chat_summary.json"
        if chat_json.exists():
            try:
                payload = json.loads(chat_json.read_text(encoding="utf-8"))
                return str(payload.get("one_line") or "未读取到 chat_summary one_line。")
            except Exception:
                return "未读取到 chat_summary one_line。"
    return "未读取到 chat_summary one_line。"


def _read_effective_data_source(result: dict[str, Any]) -> str:
    effective_path = result.get("effective_config")
    if not effective_path:
        return "unknown"
    path = Path(str(effective_path))
    if not path.exists():
        return "unknown"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return "unknown"
    return str(((payload.get("analysis", {}) or {}).get("data_source", "unknown")))
