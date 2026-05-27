from __future__ import annotations

from typing import Any

from ..workflow.config import DailyWorkflowConfig


def run_config_safety_checks(config: DailyWorkflowConfig) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    checks.append(
        _check(
            "reporter_offline",
            config.analysis.reporter == "offline",
            "warning",
            "Reporter 默认使用 offline 模式。"
            if config.analysis.reporter == "offline"
            else "当前 reporter 不是 offline，日常本地使用建议保持离线解释模式。",
            {"reporter": config.analysis.reporter},
        )
    )
    checks.append(
        _check(
            "notification_disabled_by_default",
            config.notification.enabled is False,
            "warning",
            "通知默认关闭。"
            if config.notification.enabled is False
            else "通知已启用，请确认这是你的预期。",
            {"enabled": config.notification.enabled},
        )
    )
    checks.append(
        _check(
            "notification_dry_run_default",
            config.notification.dry_run is True,
            "warning",
            "通知保持 dry_run。"
            if config.notification.dry_run is True
            else "通知 dry_run 已关闭，如使用真实通道请确认环境变量和隐私边界。",
            {"dry_run": config.notification.dry_run},
        )
    )
    if config.analysis.data_source == "manual":
        checks.append(
            _check(
                "manual_quotes_path",
                bool(config.analysis.quotes),
                "critical",
                "manual 数据源已配置 quotes 路径。"
                if config.analysis.quotes
                else "data_source=manual 时必须提供 quotes 路径。",
                {"quotes": config.analysis.quotes},
            )
        )
    elif config.analysis.data_source == "mock":
        checks.append(
            _check(
                "mock_data_source_notice",
                False,
                "warning",
                "当前使用 mock 数据源，结果更适合做结构检查。",
                {"data_source": config.analysis.data_source},
            )
        )
    elif config.analysis.data_source in {"auto", "public_fund"}:
        checks.append(
            _check(
                "external_data_notice",
                False,
                "warning",
                "当前数据源可能依赖外部公共数据，稳定性和时效性需额外确认。",
                {"data_source": config.analysis.data_source},
            )
        )
    if config.analysis.reporter == "llm":
        checks.append(
            _check(
                "llm_reporter_notice",
                False,
                "warning",
                "当前启用了 LLM reporter，建议确认不会发送真实持仓敏感信息。",
                {"reporter": config.analysis.reporter},
            )
        )
    return checks


def _check(name: str, ok: bool, severity: str, message: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "name": name,
        "ok": ok,
        "severity": severity,
        "message": message,
        "details": details or {},
    }
