from __future__ import annotations

import json
import os
from urllib.error import URLError
from urllib.request import Request, urlopen

from ..schema.errors import make_error
from .base import BaseNotifier, failure_result, success_result


class TelegramNotifier(BaseNotifier):
    name = "telegram"

    def send(self, message: dict) -> dict:
        token = os.getenv("ASSET_ANALYSIS_TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("ASSET_ANALYSIS_TELEGRAM_CHAT_ID")
        if not token or not chat_id:
            return failure_result(self.name, dry_run=False, errors=[make_error("config", "MISSING_TELEGRAM_CONFIG", "Telegram configuration is incomplete.")])
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": f"{message.get('title', '')}\n{message.get('summary', '')}",
        }
        request = Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=10):
                pass
        except (URLError, OSError, TimeoutError) as exc:
            return failure_result(self.name, dry_run=False, errors=[make_error("send", "TELEGRAM_SEND_ERROR", str(exc))])
        return success_result(self.name, message, dry_run=False)
