from __future__ import annotations

from typing import Any


def make_error(stage: str, code: str, message: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "stage": stage,
        "code": code,
        "message": message,
        "details": details or {},
    }
