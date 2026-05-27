from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..holdings_parser import _load_yaml_like

SUPPORTED_INPUT_MODES = {"alipay_csv", "holdings_yaml"}


@dataclass
class WorkflowInputConfig:
    mode: str
    alipay_csv: str = "private/alipay_holdings.local.csv"
    holdings_yaml: str = "private/holdings.local.yaml"


@dataclass
class WorkflowOutputConfig:
    daily_dir: str = "reports/daily"
    latest_dir: str = "reports/private/latest"


@dataclass
class WorkflowProfileConfig:
    name: str = "balanced"
    file: str | None = "examples/profiles/balanced.profile.yaml"


@dataclass
class WorkflowAnalysisConfig:
    data_source: str = "mock"
    reporter: str = "offline"
    rules: str | None = "examples/rules.example.yaml"
    asset_groups: str | None = "examples/asset_groups.example.yaml"
    portfolio_template: str | None = "examples/portfolio_template.example.yaml"
    overseas_exposure: str | None = "examples/overseas_exposure.example.yaml"
    quotes: str | None = "private/manual_quotes.local.csv"


@dataclass
class WorkflowNotificationConfig:
    enabled: bool = False
    config: str | None = "examples/notify.example.yaml"
    dry_run: bool = True


@dataclass
class WorkflowHistoryConfig:
    enabled: bool = True
    reports_dir: str = "reports/daily"
    index_path: str = "reports/history_index.json"
    trend_output_dir: str = "reports/trend"


@dataclass
class WorkflowChatSummaryConfig:
    enabled: bool = True
    style: str = "wechat"
    max_signals: int = 3
    max_warnings: int = 5


@dataclass
class WorkflowPreflightConfig:
    enabled: bool = True
    strict_quotes: bool = False
    fail_on_stale_quotes: bool = False
    fail_on_duplicate_codes: bool = False
    max_normal_stale_days: int = 3
    max_qdii_stale_days: int = 5


@dataclass
class DailyWorkflowConfig:
    profile: WorkflowProfileConfig
    input: WorkflowInputConfig
    output: WorkflowOutputConfig
    analysis: WorkflowAnalysisConfig
    notification: WorkflowNotificationConfig
    history: WorkflowHistoryConfig
    chat_summary: WorkflowChatSummaryConfig
    preflight: WorkflowPreflightConfig


@dataclass
class LoadedWorkflowConfigBundle:
    config: DailyWorkflowConfig
    profile: dict[str, Any] | None
    effective_config: dict[str, Any]
    warnings: list[str]


def load_workflow_config(config_path: str | Path) -> DailyWorkflowConfig:
    return load_workflow_config_bundle(config_path).config


def load_workflow_config_bundle(config_path: str | Path) -> LoadedWorkflowConfigBundle:
    path = Path(config_path)
    data = _load_yaml_like(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Workflow config root must be a mapping.")
    from ..profiles.resolver import resolve_profile_config

    resolved = resolve_profile_config(data)
    errors = resolved.get("errors", []) or []
    if errors:
        raise ValueError("; ".join(str(item.get("message", "Profile resolution failed.")) for item in errors))
    effective_config = resolved.get("effective_config", {}) or {}
    return LoadedWorkflowConfigBundle(
        config=_build_workflow_config(effective_config),
        profile=resolved.get("profile"),
        effective_config=effective_config,
        warnings=[str(item) for item in resolved.get("warnings", []) if item],
    )


def _build_workflow_config(data: dict[str, Any]) -> DailyWorkflowConfig:
    profile_raw = data.get("profile", {}) or {}
    input_raw = data.get("input", {}) or {}
    output_raw = data.get("output", {}) or {}
    analysis_raw = data.get("analysis", {}) or {}
    notification_raw = data.get("notification", {}) or {}
    history_raw = data.get("history", {}) or {}
    chat_summary_raw = data.get("chat_summary", {}) or {}
    preflight_raw = data.get("preflight", {}) or {}
    if not isinstance(profile_raw, dict) or not isinstance(input_raw, dict) or not isinstance(output_raw, dict) or not isinstance(analysis_raw, dict) or not isinstance(notification_raw, dict) or not isinstance(history_raw, dict) or not isinstance(chat_summary_raw, dict) or not isinstance(preflight_raw, dict):
        raise ValueError("Workflow config sections must be mappings.")

    mode = str(input_raw.get("mode", "")).strip()
    if mode not in SUPPORTED_INPUT_MODES:
        raise ValueError(f"Unsupported workflow input mode: {mode or 'empty'}")

    config = DailyWorkflowConfig(
        profile=WorkflowProfileConfig(
            name=str(profile_raw.get("name", "balanced") or "balanced"),
            file=_normalize_optional_path(profile_raw.get("file", "examples/profiles/balanced.profile.yaml")),
        ),
        input=WorkflowInputConfig(
            mode=mode,
            alipay_csv=str(input_raw.get("alipay_csv", "private/alipay_holdings.local.csv")),
            holdings_yaml=str(input_raw.get("holdings_yaml", "private/holdings.local.yaml")),
        ),
        output=WorkflowOutputConfig(
            daily_dir=str(output_raw.get("daily_dir", "reports/daily")),
            latest_dir=str(output_raw.get("latest_dir", "reports/private/latest")),
        ),
        analysis=WorkflowAnalysisConfig(
            data_source=str(analysis_raw.get("data_source", "mock")),
            reporter=str(analysis_raw.get("reporter", "offline")),
            rules=_normalize_optional_path(analysis_raw.get("rules", "examples/rules.example.yaml")),
            asset_groups=_normalize_optional_path(analysis_raw.get("asset_groups", "examples/asset_groups.example.yaml")),
            portfolio_template=_normalize_optional_path(analysis_raw.get("portfolio_template", "examples/portfolio_template.example.yaml")),
            overseas_exposure=_normalize_optional_path(analysis_raw.get("overseas_exposure", "examples/overseas_exposure.example.yaml")),
            quotes=_normalize_optional_path(analysis_raw.get("quotes", "private/manual_quotes.local.csv")),
        ),
        notification=WorkflowNotificationConfig(
            enabled=bool(notification_raw.get("enabled", False)),
            config=_normalize_optional_path(notification_raw.get("config", "examples/notify.example.yaml")),
            dry_run=bool(notification_raw.get("dry_run", True)),
        ),
        history=WorkflowHistoryConfig(
            enabled=bool(history_raw.get("enabled", True)),
            reports_dir=str(history_raw.get("reports_dir", "reports/daily")),
            index_path=str(history_raw.get("index_path", "reports/history_index.json")),
            trend_output_dir=str(history_raw.get("trend_output_dir", "reports/trend")),
        ),
        chat_summary=WorkflowChatSummaryConfig(
            enabled=bool(chat_summary_raw.get("enabled", True)),
            style=str(chat_summary_raw.get("style", "wechat")),
            max_signals=int(chat_summary_raw.get("max_signals", 3)),
            max_warnings=int(chat_summary_raw.get("max_warnings", 5)),
        ),
        preflight=WorkflowPreflightConfig(
            enabled=bool(preflight_raw.get("enabled", True)),
            strict_quotes=bool(preflight_raw.get("strict_quotes", False)),
            fail_on_stale_quotes=bool(preflight_raw.get("fail_on_stale_quotes", False)),
            fail_on_duplicate_codes=bool(preflight_raw.get("fail_on_duplicate_codes", False)),
            max_normal_stale_days=int(preflight_raw.get("max_normal_stale_days", 3)),
            max_qdii_stale_days=int(preflight_raw.get("max_qdii_stale_days", 5)),
        ),
    )
    return config


def _normalize_optional_path(value: Any) -> str | None:
    if value in (None, ""):
        return None
    return str(value)
