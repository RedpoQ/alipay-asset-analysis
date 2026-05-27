from __future__ import annotations

from pathlib import Path

HERMES_TASK_DIR = Path(__file__).resolve().parents[2] / "hermes_task"
SUCCESS_PROMPT_PATH = HERMES_TASK_DIR / "daily_fund_analysis_prompt.md"
FAILURE_PROMPT_PATH = HERMES_TASK_DIR / "daily_fund_analysis_failure_prompt.md"
CRONJOB_TEMPLATE_PATH = HERMES_TASK_DIR / "daily_fund_analysis.cronjob.example.yaml"
README_TEMPLATE_PATH = HERMES_TASK_DIR / "daily_fund_analysis_readme.md"

REQUIRED_SUCCESS_PROMPT_PHRASES = (
    "do not predict",
    "do not override signals",
    "read chat_summary.txt",
)

REQUIRED_FAILURE_PROMPT_PHRASES = (
    "do not invent today’s fund analysis",
    "read error output",
    "give one concrete fix command",
)


def load_prompt_template(kind: str) -> str:
    path = get_prompt_template_path(kind)
    return path.read_text(encoding="utf-8")


def get_prompt_template_path(kind: str) -> Path:
    key = kind.strip().lower()
    if key in {"success", "daily", "prompt"}:
        return SUCCESS_PROMPT_PATH
    if key in {"failure", "fail"}:
        return FAILURE_PROMPT_PATH
    raise ValueError(f"Unsupported prompt template kind: {kind}")


def missing_required_phrases(text: str, *, failure: bool = False) -> list[str]:
    haystack = text.lower()
    required = REQUIRED_FAILURE_PROMPT_PHRASES if failure else REQUIRED_SUCCESS_PROMPT_PHRASES
    return [item for item in required if item not in haystack]
