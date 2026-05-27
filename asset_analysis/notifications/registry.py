from __future__ import annotations

import argparse
import json

from ..schema.errors import make_error
from .discord import DiscordNotifier
from .dry_run import DryRunNotifier
from .email_sender import EmailNotifier
from .message_builder import build_notification_message
from .telegram import TelegramNotifier
from .webhook import WebhookNotifier


def get_notifier(channel: str):
    normalized = channel.lower()
    if normalized == "dry_run":
        return DryRunNotifier()
    if normalized == "webhook":
        return WebhookNotifier()
    if normalized == "email":
        return EmailNotifier()
    if normalized == "telegram":
        return TelegramNotifier()
    if normalized == "discord":
        return DiscordNotifier()
    raise ValueError(f"Unsupported notification channel: {channel}")


def notify_from_report(report_path: str, channel: str = "dry_run", report_md_path: str | None = None) -> dict:
    try:
        message = build_notification_message(report_path, report_md_path)
    except FileNotFoundError as exc:
        return {
            "schema_version": "1.0.0",
            "ok": False,
            "channel": channel,
            "dry_run": channel == "dry_run",
            "message": None,
            "sent_at": None,
            "errors": [make_error("read_report", "REPORT_NOT_FOUND", str(exc))],
            "warnings": [],
        }
    except Exception as exc:
        return {
            "schema_version": "1.0.0",
            "ok": False,
            "channel": channel,
            "dry_run": channel == "dry_run",
            "message": None,
            "sent_at": None,
            "errors": [make_error("read_report", "REPORT_READ_ERROR", str(exc))],
            "warnings": [],
        }

    notifier = get_notifier(channel)
    return notifier.send(message)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Send or preview asset analysis notifications from a report.json file.")
    parser.add_argument("--report", required=True, help="Path to report.json.")
    parser.add_argument("--report-md", default=None, help="Optional path to report.md.")
    parser.add_argument("--channel", choices=("dry_run", "webhook", "email", "telegram", "discord"), default="dry_run")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    result = notify_from_report(args.report, channel=args.channel, report_md_path=args.report_md)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
