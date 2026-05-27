from __future__ import annotations

from .base import ReporterOutput
from .llm_reporter import LLMReporter
from .offline_reporter import OfflineReporter


def get_reporter(mode: str | None = None):
    normalized = (mode or "offline").lower()
    if normalized == "offline":
        return OfflineReporter(mode="offline")
    if normalized == "llm":
        return LLMReporter(mode="llm")
    if normalized == "auto":
        return AutoReporter()
    raise ValueError(f"Unsupported reporter mode: {mode}")


class AutoReporter:
    name = "auto"

    def render(self, result) -> ReporterOutput:
        try:
            return LLMReporter(mode="auto").render(result)
        except Exception as exc:
            return OfflineReporter(
                mode="auto",
                fallback_warning=f"LLM reporter unavailable, offline fallback used: {exc}",
                error=str(exc),
            ).render(result)
