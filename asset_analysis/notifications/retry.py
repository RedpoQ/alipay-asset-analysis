from __future__ import annotations

import time
from typing import Any, Callable


def run_with_retry(func: Callable[[], dict[str, Any]], *, max_attempts: int = 1, backoff_seconds: int = 0) -> tuple[dict[str, Any], int]:
    attempts = 0
    last_result: dict[str, Any] | None = None
    while attempts < max_attempts:
        attempts += 1
        last_result = func()
        if last_result.get("ok"):
            return last_result, attempts
        if attempts < max_attempts and backoff_seconds > 0:
            time.sleep(backoff_seconds)
    return last_result or {"ok": False, "errors": [], "warnings": []}, attempts
