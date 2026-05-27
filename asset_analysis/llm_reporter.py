from __future__ import annotations

from .reporters.offline_reporter import OfflineReporter


def build_markdown_report(result) -> str:
    return OfflineReporter(mode="offline").render(result).report_md
