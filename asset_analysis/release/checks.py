from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
from pathlib import Path
from typing import Any

from ..hermes_adapter import run_daily_asset_analysis_task
from ..history.indexer import build_history_index
from ..history.trend_reporter import build_trend_report
from ..hermes.prompt_templates import (
    CRONJOB_TEMPLATE_PATH,
    FAILURE_PROMPT_PATH,
    SUCCESS_PROMPT_PATH,
    load_prompt_template,
    missing_required_phrases,
)
from ..demo.bundle import build_demo_bundle, scan_demo_bundle_output
from ..onboarding.init_project import init_local_project
from ..chat_summary.cli import main as chat_summary_main
from ..notifications.orchestrator import run_notification_orchestrator
from ..notify import main as notify_main
from ..openclaw_adapter import run_asset_analysis_skill
from ..pipeline import run_asset_pipeline
from ..preflight.checks import run_preflight
from ..profiles.profile_loader import BUILTIN_PROFILES, load_profile
from ..profiles.resolver import resolve_profile_config
from ..schema.constants import ASSET_ANALYSIS_SCHEMA_VERSION
from ..ux.setup_check import run_setup_check
from ..workflow.daily_run import run_daily_workflow
from ..workflow.config import load_workflow_config

REQUIRED_FILES = [
    "README.md",
    "CHANGELOG.md",
    "RELEASE_NOTES_v0.1.0-local.md",
    "VERSION",
    "requirements.txt",
    ".gitignore",
    "docs/QUICK_START.md",
    "docs/DAILY_WORKFLOW.md",
    "docs/HERMES_INTEGRATION.md",
    "docs/CONFIG_REFERENCE.md",
    "docs/PRIVACY_AND_SAFETY.md",
    "docs/MODULE_INDEX.md",
    "docs/RELEASE_CHECKLIST.md",
    "asset_analysis/pipeline.py",
    "asset_analysis/workflow/daily_run.py",
    "asset_analysis/alipay/field_aliases.py",
    "asset_analysis/alipay/normalizer.py",
    "asset_analysis/alipay/preview.py",
    "asset_analysis/onboarding/init_project.py",
    "asset_analysis/onboarding/template_writer.py",
    "asset_analysis/onboarding/repair_hints.py",
    "asset_analysis/openclaw_adapter.py",
    "asset_analysis/hermes_adapter.py",
    "asset_analysis/hermes/cronjob_runner.py",
    "asset_analysis/hermes/result_reader.py",
    "asset_analysis/hermes/prompt_templates.py",
    "asset_analysis/demo/sanitizer.py",
    "asset_analysis/demo/demo_builder.py",
    "asset_analysis/demo/bundle.py",
    "asset_analysis/demo/cli.py",
    "asset_analysis/notify.py",
    "asset_analysis/history/indexer.py",
    "asset_analysis/history/trend_reporter.py",
    "examples/rules.example.yaml",
    "examples/asset_groups.example.yaml",
    "examples/portfolio_template.example.yaml",
    "examples/notify.example.yaml",
    "examples/manual_quotes.example.csv",
    "examples/manual_quotes.example.yaml",
    "examples/profiles/conservative.profile.yaml",
    "examples/profiles/balanced.profile.yaml",
    "examples/profiles/growth.profile.yaml",
    "examples/profiles/qdii_growth.profile.yaml",
    "examples/profiles/cash_defensive.profile.yaml",
    "private/config.local.example.yaml",
    "private/alipay_holdings.local.example.csv",
    "private/holdings.local.example.yaml",
    "private/manual_quotes.local.example.csv",
    "scripts/daily_run.ps1",
    "scripts/daily_run.py",
    "hermes_task/daily_fund_analysis.cronjob.example.yaml",
    "hermes_task/daily_fund_analysis_prompt.md",
    "hermes_task/daily_fund_analysis_failure_prompt.md",
    "hermes_task/daily_fund_analysis_readme.md",
    "examples/demo/demo_holdings.yaml",
    "examples/demo/demo_manual_quotes.csv",
    "examples/demo/demo_config.yaml",
    "reports/demo/.gitkeep",
]

REQUIRED_GITIGNORE_PATTERNS = [
    "private/*.csv",
    "private/*.yaml",
    "private/*.json",
    "private/*.xlsx",
    "reports/private/",
    "reports/daily/",
    ".env",
    "*.local.yaml",
    "*.local.csv",
    "*.local.json",
]

REQUIRED_GITIGNORE_EXCEPTIONS = [
    "!private/*.example.yaml",
    "!private/*.example.csv",
    "!private/*.example.json",
]


def make_check(name: str, ok: bool, severity: str, message: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "name": name,
        "ok": ok,
        "severity": severity,
        "message": message,
        "details": details or {},
    }


def check_required_files(project_root: str | Path = ".") -> dict[str, Any]:
    base = Path(project_root)
    missing = [path for path in REQUIRED_FILES if not (base / path).exists()]
    return make_check(
        "required_files",
        ok=not missing,
        severity="critical",
        message="All required project files are present." if not missing else "Missing required project files.",
        details={"missing": missing},
    )


def check_docs_release_package(project_root: str | Path = ".") -> dict[str, Any]:
    base = Path(project_root)
    readme_path = base / "README.md"
    version_path = base / "VERSION"
    details: dict[str, Any] = {
        "missing_files": [],
        "missing_readme_phrases": [],
        "version_value": None,
        "version_ok": False,
    }
    missing_files = [
        path
        for path in [
            "docs/QUICK_START.md",
            "docs/DAILY_WORKFLOW.md",
            "docs/HERMES_INTEGRATION.md",
            "docs/CONFIG_REFERENCE.md",
            "docs/PRIVACY_AND_SAFETY.md",
            "docs/MODULE_INDEX.md",
            "docs/RELEASE_CHECKLIST.md",
            "CHANGELOG.md",
            "RELEASE_NOTES_v0.1.0-local.md",
            "VERSION",
        ]
        if not (base / path).exists()
    ]
    details["missing_files"] = missing_files

    readme_content = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""
    missing_readme_phrases = [
        phrase
        for phrase in [
            "v0.1.0-local",
            "docs/QUICK_START.md",
            "no automatic trading",
            "no prediction",
        ]
        if phrase not in readme_content
    ]
    details["missing_readme_phrases"] = missing_readme_phrases

    version_value = version_path.read_text(encoding="utf-8").strip() if version_path.exists() else None
    details["version_value"] = version_value
    details["version_ok"] = version_value == "v0.1.0-local"

    ok = not missing_files and not missing_readme_phrases and details["version_ok"]
    return make_check(
        "docs_release_package",
        ok=ok,
        severity="critical",
        message="Documentation release package is complete." if ok else "Documentation release package is incomplete.",
        details=details,
    )


def check_gitignore_privacy(project_root: str | Path = ".") -> dict[str, Any]:
    gitignore_path = Path(project_root) / ".gitignore"
    if not gitignore_path.exists():
        return make_check("privacy_gitignore", False, "critical", ".gitignore is missing.", {})
    content = gitignore_path.read_text(encoding="utf-8")
    missing_patterns = [item for item in REQUIRED_GITIGNORE_PATTERNS if item not in content]
    missing_exceptions = [item for item in REQUIRED_GITIGNORE_EXCEPTIONS if item not in content]
    ok = not missing_patterns and not missing_exceptions
    return make_check(
        "privacy_gitignore",
        ok=ok,
        severity="critical",
        message="Privacy-related .gitignore patterns are configured." if ok else "Privacy-related .gitignore patterns are incomplete.",
        details={"missing_patterns": missing_patterns, "missing_exceptions": missing_exceptions},
    )


def check_default_safety_config(config_path: str = "private/config.local.example.yaml") -> dict[str, Any]:
    path = Path(config_path)
    if not path.exists():
        return make_check("default_safety_config", False, "critical", "Default local workflow config example is missing.", {})
    config = load_workflow_config(path)
    missing: list[str] = []
    if config.analysis.data_source != "mock":
        missing.append("analysis.data_source=mock")
    if config.analysis.reporter != "offline":
        missing.append("analysis.reporter=offline")
    if config.notification.enabled is not False:
        missing.append("notification.enabled=false")
    if config.notification.dry_run is not True:
        missing.append("notification.dry_run=true")
    return make_check(
        "default_safety_config",
        ok=not missing,
        severity="critical",
        message="Default local config keeps the project in safe offline mode." if not missing else "Default local config is missing one or more safety defaults.",
        details={"missing": missing},
    )


def check_schema_constants() -> dict[str, Any]:
    ok = ASSET_ANALYSIS_SCHEMA_VERSION == "1.0.0"
    return make_check(
        "schema_constants",
        ok=ok,
        severity="critical",
        message="Schema version constant is present and matches 1.0.0." if ok else "Schema version constant is missing or unexpected.",
        details={"schema_version": ASSET_ANALYSIS_SCHEMA_VERSION},
    )


def run_python_tests_check(skip: bool = False, project_root: str | Path = ".") -> dict[str, Any]:
    if skip:
        return make_check("python_tests", True, "info", "Python test run was skipped by flag.", {"skipped": True})
    command = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"]
    completed = subprocess.run(command, cwd=Path(project_root), capture_output=True, text=True)
    return make_check(
        "python_tests",
        ok=completed.returncode == 0,
        severity="critical",
        message="Python unit tests passed." if completed.returncode == 0 else "Python unit tests failed.",
        details={"returncode": completed.returncode, "stdout": completed.stdout[-4000:], "stderr": completed.stderr[-4000:]},
    )


def run_pipeline_smoke_check(output_root: str | Path) -> dict[str, Any]:
    output_dir = Path(output_root) / "pipeline_smoke"
    run_asset_pipeline(
        input_path="examples/real_existing_holdings.yaml",
        output_dir=output_dir,
        data_source="mock",
        reporter_mode="offline",
    )
    report_json = output_dir / "report.json"
    report_md = output_dir / "report.md"
    run_json = output_dir / "run.json"
    payload = json.loads(report_json.read_text(encoding="utf-8"))
    ok = report_json.exists() and report_md.exists() and run_json.exists() and payload.get("schema_version") and payload.get("schema_errors") == []
    return make_check(
        "pipeline_smoke",
        ok=bool(ok),
        severity="critical",
        message="Pipeline smoke test passed." if ok else "Pipeline smoke test failed.",
        details={"report_json": str(report_json), "report_md": str(report_md), "run_json": str(run_json), "schema_errors": payload.get("schema_errors")},
    )


def run_manual_quote_smoke_check(output_root: str | Path) -> dict[str, Any]:
    output_dir = Path(output_root) / "manual_quote_smoke"
    run_asset_pipeline(
        input_path="examples/real_existing_holdings.yaml",
        output_dir=output_dir,
        data_source="manual",
        quotes_path="examples/manual_quotes.example.csv",
        reporter_mode="offline",
    )
    report_json = output_dir / "report.json"
    payload = json.loads(report_json.read_text(encoding="utf-8"))
    data_quality = payload.get("data_quality", {}) or {}
    ok = (
        report_json.exists()
        and isinstance(data_quality, dict)
        and data_quality.get("analysis_scope") == "manual_quote"
        and payload.get("schema_errors") == []
    )
    return make_check(
        "manual_quote_smoke",
        ok=bool(ok),
        severity="critical",
        message="Manual quote smoke test passed." if ok else "Manual quote smoke test failed.",
        details={"report_json": str(report_json), "data_quality": data_quality},
    )


def run_daily_workflow_smoke_check(output_root: str | Path) -> dict[str, Any]:
    base = Path(output_root) / "daily_workflow_smoke"
    if base.exists():
        shutil.rmtree(base)
    private_dir = base / "private"
    private_dir.mkdir(parents=True)
    reports_dir = base / "reports"
    holdings_path = private_dir / "holdings.local.yaml"
    holdings_path.write_text(Path("private/holdings.local.example.yaml").read_text(encoding="utf-8"), encoding="utf-8")
    config_path = base / "config.local.yaml"
    config_path.write_text(
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
                "  rules: examples/rules.example.yaml",
                "  asset_groups: examples/asset_groups.example.yaml",
                "  portfolio_template: examples/portfolio_template.example.yaml",
                "  quotes: private/manual_quotes.local.csv",
                "notification:",
                "  enabled: false",
                "  dry_run: true",
                "history:",
                "  enabled: true",
                f"  reports_dir: {(reports_dir / 'daily').as_posix()}",
                f"  index_path: {(reports_dir / 'history_index.json').as_posix()}",
                f"  trend_output_dir: {(reports_dir / 'trend').as_posix()}",
                "preflight:",
                "  enabled: true",
                "  strict_quotes: false",
                "  fail_on_stale_quotes: false",
            ]
        ),
        encoding="utf-8",
    )
    result = run_daily_workflow(str(config_path))
    ok = bool(result.get("ok")) and bool(result.get("report_json")) and (result.get("notification") is None or result.get("notification", {}).get("dry_run", True))
    return make_check(
        "daily_workflow_smoke",
        ok=ok,
        severity="critical",
        message="Daily workflow smoke test passed." if ok else "Daily workflow smoke test failed.",
        details=result,
    )


def run_preflight_smoke_check(output_root: str | Path) -> dict[str, Any]:
    base = Path(output_root) / "preflight_smoke"
    if base.exists():
        shutil.rmtree(base)
    private_dir = base / "private"
    private_dir.mkdir(parents=True)
    reports_dir = base / "reports"
    holdings_path = private_dir / "holdings.local.yaml"
    quotes_path = private_dir / "manual_quotes.local.csv"
    holdings_path.write_text(Path("private/holdings.local.example.yaml").read_text(encoding="utf-8"), encoding="utf-8")
    quotes_path.write_text(Path("private/manual_quotes.local.example.csv").read_text(encoding="utf-8"), encoding="utf-8")
    config_path = base / "config.local.yaml"
    config_path.write_text(
        "\n".join(
            [
                "input:",
                "  mode: holdings_yaml",
                f"  holdings_yaml: {holdings_path.as_posix()}",
                "output:",
                f"  daily_dir: {(reports_dir / 'daily').as_posix()}",
                f"  latest_dir: {(reports_dir / 'private' / 'latest').as_posix()}",
                "analysis:",
                "  data_source: manual",
                "  reporter: offline",
                f"  quotes: {quotes_path.as_posix()}",
                "notification:",
                "  enabled: false",
                "  dry_run: true",
                "preflight:",
                "  enabled: true",
            ]
        ),
        encoding="utf-8",
    )
    json_output = reports_dir / "private" / "latest" / "preflight_report.json"
    md_output = reports_dir / "private" / "latest" / "preflight_report.md"
    result = run_preflight(str(config_path), json_output=str(json_output), markdown_output=str(md_output))
    ok = bool(result.get("ok")) and json_output.exists()
    return make_check(
        "preflight_smoke",
        ok=ok,
        severity="critical",
        message="Preflight smoke test passed." if ok else "Preflight smoke test failed.",
        details={"report_json": str(json_output), "report_md": str(md_output), "summary": result.get("summary", {})},
    )


def run_profile_files_check() -> dict[str, Any]:
    missing = [path for path in BUILTIN_PROFILES.values() if not Path(path).exists()]
    return make_check(
        "profile_files",
        ok=not missing,
        severity="critical",
        message="All built-in profile files are present." if not missing else "Some built-in profile files are missing.",
        details={"missing": missing},
    )


def run_profile_loader_check() -> dict[str, Any]:
    failed: list[str] = []
    for path in BUILTIN_PROFILES.values():
        try:
            load_profile(path)
        except Exception:
            failed.append(path)
    return make_check(
        "profile_loader",
        ok=not failed,
        severity="critical",
        message="All built-in profiles can be loaded." if not failed else "Some built-in profiles failed to load.",
        details={"failed": failed},
    )


def run_profile_resolver_check() -> dict[str, Any]:
    result = resolve_profile_config({}, profile_path=BUILTIN_PROFILES["balanced"])
    ok = not result.get("errors")
    return make_check(
        "profile_resolver",
        ok=ok,
        severity="critical",
        message="Balanced profile resolves successfully." if ok else "Balanced profile failed to resolve.",
        details={"profile": result.get("profile"), "errors": result.get("errors", [])},
    )


def run_profile_workflow_smoke_check(output_root: str | Path) -> dict[str, Any]:
    base = Path(output_root) / "profile_workflow_smoke"
    if base.exists():
        shutil.rmtree(base)
    private_dir = base / "private"
    private_dir.mkdir(parents=True)
    reports_dir = base / "reports"
    holdings_path = private_dir / "holdings.local.yaml"
    holdings_path.write_text(Path("private/holdings.local.example.yaml").read_text(encoding="utf-8"), encoding="utf-8")
    config_path = base / "config.local.yaml"
    config_path.write_text(
        "\n".join(
            [
                "profile:",
                "  name: balanced",
                "  file: examples/profiles/balanced.profile.yaml",
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
                "  dry_run: true",
                "preflight:",
                "  enabled: true",
            ]
        ),
        encoding="utf-8",
    )
    result = run_daily_workflow(str(config_path))
    effective_path = result.get("effective_config")
    ok = bool(result.get("ok")) and bool(effective_path) and Path(str(effective_path)).exists()
    return make_check(
        "profile_workflow_smoke",
        ok=ok,
        severity="critical",
        message="Profile workflow smoke test passed." if ok else "Profile workflow smoke test failed.",
        details={"profile": result.get("profile"), "effective_config": effective_path, "warnings": result.get("warnings", [])},
    )


def run_setup_check_smoke_check(output_root: str | Path) -> dict[str, Any]:
    base = Path(output_root) / "setup_check_smoke"
    if base.exists():
        shutil.rmtree(base)
    private_dir = base / "private"
    private_dir.mkdir(parents=True)
    reports_dir = base / "reports"
    csv_path = private_dir / "alipay_holdings.local.csv"
    csv_path.write_text(Path("private/alipay_holdings.local.example.csv").read_text(encoding="utf-8"), encoding="utf-8")
    config_path = base / "config.local.yaml"
    config_path.write_text(
        "\n".join(
            [
                "profile:",
                "  name: balanced",
                "  file: examples/profiles/balanced.profile.yaml",
                "input:",
                "  mode: alipay_csv",
                f"  alipay_csv: {csv_path.as_posix()}",
                f"  holdings_yaml: {(private_dir / 'holdings.local.yaml').as_posix()}",
                "output:",
                f"  daily_dir: {(reports_dir / 'daily').as_posix()}",
                f"  latest_dir: {(reports_dir / 'private' / 'latest').as_posix()}",
                "analysis:",
                "  data_source: mock",
                "  reporter: offline",
                "notification:",
                "  enabled: false",
                "  dry_run: true",
            ]
        ),
        encoding="utf-8",
    )
    markdown_path = reports_dir / "private" / "latest" / "setup_check.md"
    result = run_setup_check(str(config_path), markdown_output=str(markdown_path))
    ok = bool(result.get("ok")) and markdown_path.exists()
    return make_check(
        "setup_check_smoke",
        ok=ok,
        severity="critical",
        message="Setup check smoke test passed." if ok else "Setup check smoke test failed.",
        details={"markdown": str(markdown_path), "summary": result.get("summary", {})},
    )


def run_onboarding_init_smoke_check(output_root: str | Path) -> dict[str, Any]:
    base = Path(output_root) / "onboarding_init_smoke"
    if base.exists():
        shutil.rmtree(base)
    base.mkdir(parents=True)
    (base / "private").mkdir()
    (base / "examples").mkdir()
    (base / "examples" / "profiles").mkdir(parents=True, exist_ok=True)
    for source, target in [
        ("private/alipay_holdings.local.example.csv", base / "private" / "alipay_holdings.local.example.csv"),
        ("private/manual_quotes.local.example.csv", base / "private" / "manual_quotes.local.example.csv"),
        ("private/holdings.local.example.yaml", base / "private" / "holdings.local.example.yaml"),
        ("examples/profiles/balanced.profile.yaml", base / "examples" / "profiles" / "balanced.profile.yaml"),
    ]:
        target.write_text(Path(source).read_text(encoding="utf-8"), encoding="utf-8")
    result = init_local_project(project_root=base, dry_run=True, profile="balanced", data_source="mock")
    ok = bool(result.get("ok")) and bool(result.get("created"))
    return make_check(
        "onboarding_init_smoke",
        ok=ok,
        severity="critical",
        message="Onboarding init dry-run smoke test passed." if ok else "Onboarding init dry-run smoke test failed.",
        details=result,
    )


def run_alipay_preview_smoke_check(output_root: str | Path) -> dict[str, Any]:
    from ..alipay.preview import build_preview_payload

    sample = Path("private/alipay_holdings.local.example.csv")
    if not sample.exists():
        sample = Path("examples/alipay_holdings.example.csv")
    payload = build_preview_payload(sample)
    ok = bool(payload.get("canonical_field_mapping")) and payload.get("valid_rows_count", 0) > 0
    return make_check(
        "alipay_preview_smoke",
        ok=ok,
        severity="critical",
        message="Alipay preview smoke test passed." if ok else "Alipay preview smoke test failed.",
        details={"input": str(sample), "mapping": payload.get("canonical_field_mapping", {}), "valid_rows_count": payload.get("valid_rows_count", 0)},
    )


def run_setup_repair_hints_smoke_check(output_root: str | Path) -> dict[str, Any]:
    missing_config = Path(output_root) / "repair_hints_smoke" / "missing.local.yaml"
    result = run_setup_check(str(missing_config))
    hints = result.get("repair_hints", []) or []
    ok = any(item.get("problem") == "missing_config" for item in hints)
    return make_check(
        "setup_repair_hints_smoke",
        ok=ok,
        severity="critical",
        message="Setup repair hints smoke test passed." if ok else "Setup repair hints smoke test failed.",
        details={"repair_hints": hints},
    )


def check_hermes_prompt_templates() -> dict[str, Any]:
    success_text = load_prompt_template("success")
    failure_text = load_prompt_template("failure")
    success_missing = missing_required_phrases(success_text)
    failure_missing = missing_required_phrases(failure_text, failure=True)
    ok = not success_missing and not failure_missing
    return make_check(
        "hermes_prompt_templates",
        ok=ok,
        severity="critical",
        message="Hermes prompt templates contain the required safety instructions." if ok else "Hermes prompt templates are missing required safety instructions.",
        details={
            "cronjob_template": str(CRONJOB_TEMPLATE_PATH),
            "success_prompt": str(SUCCESS_PROMPT_PATH),
            "failure_prompt": str(FAILURE_PROMPT_PATH),
            "missing_success_phrases": success_missing,
            "missing_failure_phrases": failure_missing,
        },
    )


def run_hermes_cronjob_runner_smoke_check(output_root: str | Path) -> dict[str, Any]:
    base = Path(output_root) / "hermes_cronjob_runner_smoke"
    if base.exists():
        shutil.rmtree(base)
    private_dir = base / "private"
    private_dir.mkdir(parents=True)
    reports_dir = base / "reports"
    holdings_path = private_dir / "holdings.local.yaml"
    holdings_path.write_text(Path("private/holdings.local.example.yaml").read_text(encoding="utf-8"), encoding="utf-8")
    config_path = base / "config.local.yaml"
    config_path.write_text(
        "\n".join(
            [
                "profile:",
                "  name: balanced",
                "  file: examples/profiles/balanced.profile.yaml",
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
                "  dry_run: true",
                "preflight:",
                "  enabled: true",
            ]
        ),
        encoding="utf-8",
    )
    command = [
        sys.executable,
        "-m",
        "asset_analysis.hermes.cronjob_runner",
        "--config",
        str(config_path),
        "--latest-dir",
        str(reports_dir / "private" / "latest"),
        "--json-only",
    ]
    completed = subprocess.run(command, cwd=Path("."), capture_output=True, text=True)
    payload: dict[str, Any] = {}
    try:
        payload = json.loads(completed.stdout)
    except Exception:
        payload = {}
    ok = completed.returncode == 0 and bool(payload.get("ok")) and bool(payload.get("chat_summary"))
    return make_check(
        "hermes_cronjob_runner_smoke",
        ok=ok,
        severity="critical",
        message="Hermes cronjob runner smoke test passed." if ok else "Hermes cronjob runner smoke test failed.",
        details={"returncode": completed.returncode, "stdout": completed.stdout[-2000:], "stderr": completed.stderr[-2000:]},
    )


def run_demo_bundle_smoke_check(output_root: str | Path) -> dict[str, Any]:
    source_report = Path(output_root) / "pipeline_smoke" / "report.json"
    demo_dir = Path(output_root) / "demo_bundle_smoke"
    result = build_demo_bundle(source_report_path=str(source_report), output_dir=str(demo_dir), mode="public", force=True)
    scan_findings = scan_demo_bundle_output(demo_dir) if result.get("ok") else []
    ok = (
        bool(result.get("ok"))
        and not scan_findings
        and Path(result.get("files", {}).get("demo_report_json", "")).exists()
        and Path(result.get("files", {}).get("demo_chat_summary_txt", "")).exists()
    )
    return make_check(
        "demo_bundle_smoke",
        ok=ok,
        severity="critical",
        message="Demo bundle smoke test passed." if ok else "Demo bundle smoke test failed.",
        details={"result": result, "scan_findings": scan_findings},
    )


def run_notify_dry_run_smoke_check(output_root: str | Path) -> dict[str, Any]:
    report_path = Path(output_root) / "pipeline_smoke" / "report.json"
    sink = StringIO()
    with redirect_stdout(sink), redirect_stderr(sink):
        result_code = notify_main(["--report", str(report_path), "--channel", "dry_run"])
    ok = result_code == 0
    return make_check(
        "notify_dry_run_smoke",
        ok=ok,
        severity="critical",
        message="Notification dry-run smoke test passed." if ok else "Notification dry-run smoke test failed.",
        details={"report": str(report_path), "returncode": result_code, "channel": "dry_run", "stdout": sink.getvalue()[-2000:]},
    )


def run_notification_orchestrator_dry_run_smoke_check(output_root: str | Path) -> dict[str, Any]:
    report_path = Path(output_root) / "pipeline_smoke" / "report.json"
    result = run_notification_orchestrator(
        report_path=str(report_path),
        channels=["dry_run"],
        dry_run=True,
    )
    ok = bool(result.get("ok")) and "dry_run" in result.get("selected_channels", [])
    return make_check(
        "notification_orchestrator_dry_run_smoke",
        ok=ok,
        severity="critical",
        message="Notification orchestrator dry-run smoke test passed." if ok else "Notification orchestrator dry-run smoke test failed.",
        details={"selected_channels": result.get("selected_channels", []), "summary": result.get("summary", {}), "warnings": result.get("warnings", [])},
    )


def run_chat_summary_smoke_check(output_root: str | Path) -> dict[str, Any]:
    report_path = Path(output_root) / "pipeline_smoke" / "report.json"
    output_path = Path(output_root) / "chat_summary_smoke.txt"
    result_code = chat_summary_main(["--report", str(report_path), "--output", str(output_path)])
    content = output_path.read_text(encoding="utf-8") if output_path.exists() else ""
    banned_phrases = [
        "Current position",
        "exceeds max_single_position",
        "rebalance band",
        "overweight band",
    ]
    ok = (
        result_code == 0
        and output_path.exists()
        and "规则驱动" in content
        and "不预测" in content
        and not any(phrase in content for phrase in banned_phrases)
    )
    return make_check(
        "chat_summary_smoke",
        ok=ok,
        severity="critical",
        message="Chat summary smoke test passed." if ok else "Chat summary smoke test failed.",
        details={"output": str(output_path), "returncode": result_code},
    )


def run_openclaw_smoke_check(output_root: str | Path) -> dict[str, Any]:
    result = run_asset_analysis_skill(
        holdings_path="examples/real_existing_holdings.yaml",
        output_dir=str(Path(output_root) / "openclaw_smoke"),
        data_source="mock",
        reporter="offline",
    )
    ok = bool(result.get("ok")) and bool(result.get("schema_version"))
    return make_check(
        "openclaw_smoke",
        ok=ok,
        severity="critical",
        message="OpenClaw adapter smoke test passed." if ok else "OpenClaw adapter smoke test failed.",
        details={"schema_version": result.get("schema_version"), "report_json": result.get("report_json")},
    )


def run_hermes_smoke_check(output_root: str | Path) -> dict[str, Any]:
    result = run_daily_asset_analysis_task(
        holdings_path="examples/real_existing_holdings.yaml",
        output_dir=str(Path(output_root) / "hermes_smoke"),
        data_source="mock",
        reporter="offline",
    )
    daily_message = str(result.get("daily_message", ""))
    ok = bool(result.get("ok")) and result.get("task") == "daily_asset_analysis" and "规则驱动" in daily_message
    return make_check(
        "hermes_smoke",
        ok=ok,
        severity="critical",
        message="Hermes adapter smoke test passed." if ok else "Hermes adapter smoke test failed.",
        details={"task": result.get("task"), "daily_message": daily_message},
    )


def run_history_smoke_check() -> dict[str, Any]:
    reports_dir = Path("reports/daily")
    if not reports_dir.exists() or not list(reports_dir.glob("*/report.json")):
        return make_check(
            "history_smoke",
            ok=False,
            severity="warning",
            message="No daily history was available yet; history smoke test was skipped.",
            details={"reports_dir": str(reports_dir)},
        )
    index_payload = build_history_index(str(reports_dir), "reports/history_index.json")
    trend_payload = build_trend_report(index_path="reports/history_index.json", output_path="reports/trend/latest_trend.md")
    ok = Path("reports/history_index.json").exists() and bool(trend_payload.get("output_path"))
    return make_check(
        "history_smoke",
        ok=ok,
        severity="warning",
        message="History smoke test passed." if ok else "History smoke test failed.",
        details={"count": index_payload.get("count"), "trend_output": trend_payload.get("output_path")},
    )
