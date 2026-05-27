from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from ..chat_summary.builder import build_chat_summary
from ..chat_summary.formatter import format_chat_summary
from ..schema.constants import ASSET_ANALYSIS_SCHEMA_VERSION
from .demo_builder import (
    build_builtin_demo_payload,
    build_sanitized_report_payload,
    render_demo_readme,
    render_demo_report_markdown,
)
from .sanitizer import sanitize_generic_payload, scan_text_for_sensitive_strings


def build_demo_bundle(
    source_report_path: str | None = None,
    output_dir: str = "reports/demo",
    mode: str = "public",
    *,
    force: bool = False,
) -> dict[str, Any]:
    output_path = Path(output_dir)
    warnings: list[str] = []
    errors: list[dict[str, str]] = []
    if _is_unsafe_output_dir(output_path):
        return _failure(mode, output_dir, "output_dir", f"Refusing to write demo bundle outside a demo-safe directory: {output_dir}")
    output_path.mkdir(parents=True, exist_ok=True)
    _ensure_demo_output_can_be_written(output_path, force=force)

    preflight_payload: dict[str, Any] | None = None
    try:
        if source_report_path:
            sanitized_report = build_sanitized_report_payload(source_report_path, mode=mode)
        else:
            sanitized_report, preflight_payload = build_builtin_demo_payload(output_path, mode=mode)
    except Exception as exc:
        return _failure(mode, output_dir, "build_demo", str(exc))

    files = {
        "demo_report_json": str(output_path / "demo_report.json"),
        "demo_report_md": str(output_path / "demo_report.md"),
        "demo_chat_summary_txt": str(output_path / "demo_chat_summary.txt"),
        "demo_chat_summary_md": str(output_path / "demo_chat_summary.md"),
        "demo_readme": str(output_path / "README_DEMO.md"),
    }
    if preflight_payload is not None:
        files["demo_preflight_report_json"] = str(output_path / "demo_preflight_report.json")

    Path(files["demo_report_json"]).write_text(json.dumps(sanitized_report, ensure_ascii=False, indent=2), encoding="utf-8")
    Path(files["demo_report_md"]).write_text(render_demo_report_markdown(sanitized_report), encoding="utf-8")

    chat_summary = build_chat_summary(files["demo_report_json"])
    chat_summary_txt = format_chat_summary(chat_summary, format="text")
    chat_summary_md = format_chat_summary(chat_summary, format="markdown")
    Path(files["demo_chat_summary_txt"]).write_text(chat_summary_txt, encoding="utf-8")
    Path(files["demo_chat_summary_md"]).write_text(chat_summary_md, encoding="utf-8")

    if preflight_payload is not None:
        sanitized_preflight = sanitize_generic_payload(preflight_payload)
        Path(files["demo_preflight_report_json"]).write_text(json.dumps(sanitized_preflight, ensure_ascii=False, indent=2), encoding="utf-8")

    Path(files["demo_readme"]).write_text(
        render_demo_readme(
            mode=mode,
            files=files,
            chat_summary_text=chat_summary_txt,
            source_report_path=source_report_path,
        ),
        encoding="utf-8",
    )

    temp_workflow_dir = output_path / "_demo_workflow"
    if temp_workflow_dir.exists():
        shutil.rmtree(temp_workflow_dir)

    scan_findings = scan_demo_bundle_output(output_path)
    if scan_findings:
        return {
            "schema_version": ASSET_ANALYSIS_SCHEMA_VERSION,
            "ok": False,
            "mode": mode,
            "output_dir": str(output_path),
            "files": files,
            "errors": [{"stage": "scan_output", "message": f"Sensitive strings detected: {', '.join(scan_findings)}"}],
            "warnings": warnings,
        }

    return {
        "schema_version": ASSET_ANALYSIS_SCHEMA_VERSION,
        "ok": True,
        "mode": mode,
        "output_dir": str(output_path),
        "files": files,
        "errors": errors,
        "warnings": warnings,
    }


def scan_demo_bundle_output(output_dir: str | Path) -> list[str]:
    base = Path(output_dir)
    findings: list[str] = []
    for path in base.rglob("*"):
        if path.is_dir():
            continue
        if path.name == ".gitkeep":
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            continue
        for item in scan_text_for_sensitive_strings(text):
            if item not in findings:
                findings.append(item)
    return findings


def _ensure_demo_output_can_be_written(output_path: Path, *, force: bool) -> None:
    managed_files = {
        "demo_report.json",
        "demo_report.md",
        "demo_chat_summary.txt",
        "demo_chat_summary.md",
        "demo_preflight_report.json",
        "README_DEMO.md",
    }
    if force:
        for name in managed_files:
            target = output_path / name
            if target.exists():
                target.unlink()
        temp_root = output_path / "_demo_workflow"
        if temp_root.exists():
            shutil.rmtree(temp_root)
        return
    for name in managed_files:
        target = output_path / name
        if target.exists():
            raise FileExistsError(f"Demo bundle output already exists: {target}. Use --force to overwrite demo files.")


def _is_unsafe_output_dir(path: Path) -> bool:
    normalized = str(path).replace("\\", "/").lower()
    return "/private" in normalized or normalized.endswith("/private") or normalized.endswith("/reports/private")


def _failure(mode: str, output_dir: str, stage: str, message: str) -> dict[str, Any]:
    return {
        "schema_version": ASSET_ANALYSIS_SCHEMA_VERSION,
        "ok": False,
        "mode": mode,
        "output_dir": output_dir,
        "files": {},
        "errors": [{"stage": stage, "message": message}],
        "warnings": [],
    }
