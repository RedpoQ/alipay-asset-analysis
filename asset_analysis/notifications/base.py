from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any

from ..schema.constants import ASSET_ANALYSIS_SCHEMA_VERSION


def notification_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def success_result(channel: str, message: dict[str, Any], *, dry_run: bool, warnings: list[str] | None = None) -> dict[str, Any]:
    return {
        "schema_version": ASSET_ANALYSIS_SCHEMA_VERSION,
        "ok": True,
        "channel": channel,
        "dry_run": dry_run,
        "message": message,
        "sent_at": None if dry_run else notification_timestamp(),
        "errors": [],
        "warnings": warnings or [],
    }


def failure_result(channel: str, *, dry_run: bool, errors: list[dict[str, Any]], warnings: list[str] | None = None) -> dict[str, Any]:
    return {
        "schema_version": ASSET_ANALYSIS_SCHEMA_VERSION,
        "ok": False,
        "channel": channel,
        "dry_run": dry_run,
        "message": None,
        "sent_at": None,
        "errors": errors,
        "warnings": warnings or [],
    }


class BaseNotifier(ABC):
    name = "base"
    dry_run = False

    @abstractmethod
    def send(self, message: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError
