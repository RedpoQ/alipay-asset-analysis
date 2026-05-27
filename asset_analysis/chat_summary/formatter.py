from __future__ import annotations

from typing import Any


def format_chat_summary(summary: dict[str, Any], format: str = "text") -> str:
    if format == "markdown":
        return _format_markdown(summary)
    return _format_text(summary)


def _format_text(summary: dict[str, Any]) -> str:
    lines = [str(summary.get("title", "每日基金分析")), str(summary.get("one_line", ""))]
    for section in summary.get("sections", []):
        lines.append(section.get("title", ""))
        for item in section.get("items", []):
            lines.append(f"- {item}")
    return "\n".join(line for line in lines if line).strip() + "\n"


def _format_markdown(summary: dict[str, Any]) -> str:
    lines = [f"# {summary.get('title', '每日基金分析')}", "", summary.get("one_line", "")]
    for section in summary.get("sections", []):
        lines.extend(["", f"## {section.get('title', '')}"])
        for item in section.get("items", []):
            lines.append(f"- {item}")
    return "\n".join(lines).strip() + "\n"
