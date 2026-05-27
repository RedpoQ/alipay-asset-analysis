from __future__ import annotations

import argparse
import json
from typing import Any

from ..schema.constants import ASSET_ANALYSIS_SCHEMA_VERSION
from ..schema.errors import make_error
from .config import channel_retry_map, enabled_channels, load_notification_config
from .message_builder import build_notification_message, load_report_payload
from .registry import get_notifier
from .retry import run_with_retry

NETWORK_CHANNELS = {"webhook", "email", "telegram", "discord"}


def run_notification_orchestrator(
    report_path: str,
    config_path: str | None = None,
    channels: list[str] | None = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    try:
        report_payload = load_report_payload(report_path)
    except FileNotFoundError as exc:
        return _failure([make_error("read_report", "REPORT_NOT_FOUND", str(exc))], report_path, dry_run)
    except Exception as exc:
        return _failure([make_error("read_report", "REPORT_READ_ERROR", str(exc))], report_path, dry_run)

    try:
        config = load_notification_config(config_path)
    except Exception as exc:
        return _failure([make_error("config", "CONFIG_ERROR", str(exc))], report_path, dry_run)

    try:
        message = build_notification_message(report_path)
    except Exception as exc:
        return _failure([make_error("read_report", "MESSAGE_BUILD_ERROR", str(exc))], report_path, dry_run)

    selected = channels[:] if channels else _select_channels_from_config(report_payload, config)
    if not selected:
        selected = ["dry_run"]
    retries = channel_retry_map(config)
    enabled = enabled_channels(config)
    warnings: list[str] = []
    results: list[dict[str, Any]] = []

    for channel in selected:
        if channel not in enabled and not (dry_run and channel == "dry_run"):
            results.append({"channel": channel, "ok": False, "attempts": 0, "errors": [make_error("config", "CHANNEL_DISABLED", f"Channel is disabled: {channel}")], "warnings": []})
            continue

        if dry_run and channel in NETWORK_CHANNELS:
            warnings.append(f"Skipped network channel '{channel}' because dry_run=True.")
            results.append({"channel": channel, "ok": False, "attempts": 0, "errors": [], "warnings": ["skipped_by_dry_run"], "skipped": True})
            continue

        if not dry_run and channel in NETWORK_CHANNELS and not config.safety.allow_network_channels:
            warnings.append(f"Skipped network channel '{channel}' because allow_network_channels=false.")
            results.append({"channel": channel, "ok": False, "attempts": 0, "errors": [], "warnings": ["skipped_by_safety_policy"], "skipped": True})
            continue

        notifier_channel = "dry_run" if dry_run and channel == "dry_run" else channel
        notifier = get_notifier(notifier_channel)
        retry = retries.get(channel)
        result, attempts = run_with_retry(
            lambda: notifier.send(message),
            max_attempts=retry.max_attempts if retry else 1,
            backoff_seconds=retry.backoff_seconds if retry else 0,
        )
        results.append(
            {
                "channel": channel,
                "ok": bool(result.get("ok")),
                "attempts": attempts,
                "errors": list(result.get("errors", [])),
                "warnings": list(result.get("warnings", [])),
            }
        )

    summary = _summarize(results)
    ok = summary["succeeded"] > 0 and summary["failed"] < summary["total"] or (summary["total"] == 1 and summary["succeeded"] == 1)
    if summary["succeeded"] == 0:
        ok = False
    return {
        "schema_version": ASSET_ANALYSIS_SCHEMA_VERSION,
        "ok": ok,
        "report": report_path,
        "dry_run": dry_run,
        "selected_channels": selected,
        "results": results,
        "summary": summary,
        "errors": [] if ok or summary["total"] > 0 else [make_error("unknown", "NO_CHANNELS", "No channels were selected.")],
        "warnings": warnings,
    }


def _select_channels_from_config(report_payload: dict[str, Any], config) -> list[str]:
    selected = list(config.routing.default_channels)
    if report_payload.get("portfolio_warnings"):
        selected.extend(config.routing.on_portfolio_warning)
    if any(str(signal.get("signal")) == "reduce" for signal in report_payload.get("signals", [])):
        selected.extend(config.routing.on_reduce_signal)
    deduped: list[str] = []
    for channel in selected:
        if channel not in deduped:
            deduped.append(channel)
    return deduped


def _summarize(results: list[dict[str, Any]]) -> dict[str, int]:
    summary = {"total": len(results), "succeeded": 0, "failed": 0, "skipped": 0}
    for result in results:
        if result.get("skipped"):
            summary["skipped"] += 1
        elif result.get("ok"):
            summary["succeeded"] += 1
        else:
            summary["failed"] += 1
    return summary


def _failure(errors: list[dict[str, Any]], report_path: str, dry_run: bool) -> dict[str, Any]:
    return {
        "schema_version": ASSET_ANALYSIS_SCHEMA_VERSION,
        "ok": False,
        "report": report_path,
        "dry_run": dry_run,
        "selected_channels": [],
        "results": [],
        "summary": {"total": 0, "succeeded": 0, "failed": 0, "skipped": 0},
        "errors": errors,
        "warnings": [],
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Orchestrate notifications for one asset analysis report.")
    parser.add_argument("--report", required=True, help="Path to report.json.")
    parser.add_argument("--config", default=None, help="Optional notification config YAML.")
    parser.add_argument("--channels", nargs="*", default=None, help="Optional explicit channels override.")
    parser.add_argument("--dry-run", action=argparse.BooleanOptionalAction, default=True, help="Preview mode that never sends network channels.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    result = run_notification_orchestrator(
        report_path=args.report,
        config_path=args.config,
        channels=args.channels,
        dry_run=args.dry_run,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
