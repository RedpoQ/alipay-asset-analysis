from __future__ import annotations

from typing import Any


def build_repair_hints(
    checks: list[dict[str, Any]],
    *,
    config_path: str = "private/config.local.yaml",
    data_source: str | None = None,
) -> list[dict[str, str]]:
    hints: list[dict[str, str]] = []

    def add(problem: str, suggestion: str) -> None:
        entry = {"problem": problem, "suggestion": suggestion}
        if entry not in hints:
            hints.append(entry)

    for check in checks:
        name = str(check.get("name", ""))
        details = check.get("details", {}) or {}
        if name == "config_exists" and not check.get("ok"):
            add("missing_config", "Run python -m asset_analysis.onboarding.init_project")
        elif name == "alipay_csv_exists" and not check.get("ok"):
            path = str(details.get("path") or "private/alipay_holdings.local.csv")
            add("missing_alipay_csv", f"Create or copy {path}, or run python -m asset_analysis.onboarding.init_project")
        elif name == "manual_quotes_exists" and not check.get("ok"):
            path = str(details.get("path") or "private/manual_quotes.local.csv")
            default_suggestion = r"copy private\manual_quotes.local.example.csv private\manual_quotes.local.csv"
            add("missing_manual_quotes", default_suggestion if path.endswith("private/manual_quotes.local.csv") or path.endswith("private\\manual_quotes.local.csv") else f"Create the missing file: {path}")
        elif name == "holdings_yaml_exists" and not check.get("ok"):
            path = str(details.get("path") or "private/holdings.local.yaml")
            add("missing_holdings_yaml", f"Create the missing file referenced by config: {path}")
        elif name == "alipay_csv_headers_known" and not check.get("ok"):
            path = str(details.get("path") or "private/alipay_holdings.local.csv")
            add("unknown_csv_headers", f"Run python -m asset_analysis.alipay.preview --input {path}")
        elif name == "config_file_reference_missing" and not check.get("ok"):
            path = str(details.get("path") or "")
            if path:
                add("missing_config_path_reference", f"Fix the config path or create the missing file: {path}")

    if not hints and data_source == "manual":
        add("manual_quotes_review", "Confirm private/manual_quotes.local.csv is updated before running the manual quote workflow")
    return hints
