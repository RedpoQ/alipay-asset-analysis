from __future__ import annotations

import json
import os
from urllib.error import URLError
from urllib.request import Request, urlopen

from ..schema.errors import make_error
from .base import BaseNotifier, failure_result, success_result


class WebhookNotifier(BaseNotifier):
    name = "webhook"

    def send(self, message: dict) -> dict:
        url = os.getenv("ASSET_ANALYSIS_WEBHOOK_URL")
        if not url:
            return failure_result(self.name, dry_run=False, errors=[make_error("config", "MISSING_WEBHOOK_URL", "ASSET_ANALYSIS_WEBHOOK_URL is not set.")])
        request = Request(
            url,
            data=json.dumps(message).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=10):
                pass
        except (URLError, OSError, TimeoutError) as exc:
            return failure_result(self.name, dry_run=False, errors=[make_error("send", "WEBHOOK_SEND_ERROR", str(exc))])
        return success_result(self.name, message, dry_run=False)
