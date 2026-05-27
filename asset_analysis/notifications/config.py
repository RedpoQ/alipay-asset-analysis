from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..holdings_parser import _load_yaml_like
from ..schema.errors import make_error

SUPPORTED_CHANNELS = {"dry_run", "webhook", "email", "telegram", "discord"}


@dataclass
class RetryConfig:
    max_attempts: int = 1
    backoff_seconds: int = 0


@dataclass
class ChannelConfig:
    name: str
    enabled: bool = False
    retry: RetryConfig = field(default_factory=RetryConfig)


@dataclass
class RoutingConfig:
    default_channels: list[str] = field(default_factory=lambda: ["dry_run"])
    on_portfolio_warning: list[str] = field(default_factory=lambda: ["dry_run"])
    on_reduce_signal: list[str] = field(default_factory=lambda: ["dry_run"])


@dataclass
class SafetyConfig:
    dry_run_default: bool = True
    allow_network_channels: bool = False


@dataclass
class NotificationConfig:
    channels: list[ChannelConfig] = field(default_factory=lambda: [ChannelConfig(name="dry_run", enabled=True)])
    routing: RoutingConfig = field(default_factory=RoutingConfig)
    safety: SafetyConfig = field(default_factory=SafetyConfig)


def load_notification_config(config_path: str | None = None) -> NotificationConfig:
    if config_path is None:
        return NotificationConfig()
    path = Path(config_path)
    data = _load_yaml_like(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Notification config must be a mapping.")
    return _build_notification_config(data)


def validate_notification_config(config: NotificationConfig) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    seen = set()
    for channel in config.channels:
        if channel.name not in SUPPORTED_CHANNELS:
            errors.append(make_error("config", "UNKNOWN_CHANNEL", f"Unsupported channel: {channel.name}", {"channel": channel.name}))
        if not isinstance(channel.enabled, bool):
            errors.append(make_error("config", "INVALID_ENABLED", "enabled must be boolean.", {"channel": channel.name}))
        if channel.retry.max_attempts < 1:
            errors.append(make_error("config", "INVALID_RETRY_ATTEMPTS", "retry.max_attempts must be >= 1.", {"channel": channel.name}))
        if channel.name in seen:
            errors.append(make_error("config", "DUPLICATE_CHANNEL", f"Duplicate channel config: {channel.name}", {"channel": channel.name}))
        seen.add(channel.name)
    return errors


def channel_retry_map(config: NotificationConfig) -> dict[str, RetryConfig]:
    return {channel.name: channel.retry for channel in config.channels}


def enabled_channels(config: NotificationConfig) -> set[str]:
    return {channel.name for channel in config.channels if channel.enabled}


def _build_notification_config(data: dict[str, Any]) -> NotificationConfig:
    channels_raw = data.get("channels", [])
    if not isinstance(channels_raw, list):
        raise ValueError("channels must be a list.")
    channels: list[ChannelConfig] = []
    for item in channels_raw:
        if not isinstance(item, dict):
            raise ValueError("Each channel config must be a mapping.")
        retry_raw = item.get("retry", {}) or {}
        if not isinstance(retry_raw, dict):
            raise ValueError("retry must be a mapping.")
        channels.append(
            ChannelConfig(
                name=str(item.get("name", "")),
                enabled=item.get("enabled", False),
                retry=RetryConfig(
                    max_attempts=int(retry_raw.get("max_attempts", 1)),
                    backoff_seconds=int(retry_raw.get("backoff_seconds", 0)),
                ),
            )
        )

    routing_raw = data.get("routing", {}) or {}
    safety_raw = data.get("safety", {}) or {}
    config = NotificationConfig(
        channels=channels or [ChannelConfig(name="dry_run", enabled=True)],
        routing=RoutingConfig(
            default_channels=list(routing_raw.get("default_channels", ["dry_run"])),
            on_portfolio_warning=list(routing_raw.get("on_portfolio_warning", [])),
            on_reduce_signal=list(routing_raw.get("on_reduce_signal", [])),
        ),
        safety=SafetyConfig(
            dry_run_default=bool(safety_raw.get("dry_run_default", True)),
            allow_network_channels=bool(safety_raw.get("allow_network_channels", False)),
        ),
    )
    errors = validate_notification_config(config)
    if errors:
        raise ValueError(str(errors))
    return config
