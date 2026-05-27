from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage

from ..schema.errors import make_error
from .base import BaseNotifier, failure_result, success_result


class EmailNotifier(BaseNotifier):
    name = "email"

    def send(self, message: dict) -> dict:
        config = {
            "host": os.getenv("ASSET_ANALYSIS_SMTP_HOST"),
            "port": os.getenv("ASSET_ANALYSIS_SMTP_PORT"),
            "user": os.getenv("ASSET_ANALYSIS_SMTP_USER"),
            "password": os.getenv("ASSET_ANALYSIS_SMTP_PASSWORD"),
            "from": os.getenv("ASSET_ANALYSIS_EMAIL_FROM"),
            "to": os.getenv("ASSET_ANALYSIS_EMAIL_TO"),
        }
        missing = [key for key, value in config.items() if not value]
        if missing:
            return failure_result(self.name, dry_run=False, errors=[make_error("config", "MISSING_EMAIL_CONFIG", "Missing email configuration.", {"missing": missing})])

        email = EmailMessage()
        email["Subject"] = message.get("title", "Daily Asset Analysis")
        email["From"] = config["from"]
        email["To"] = config["to"]
        email.set_content(message.get("summary", ""))
        try:
            with smtplib.SMTP(config["host"], int(config["port"]), timeout=10) as client:
                client.starttls()
                client.login(config["user"], config["password"])
                client.send_message(email)
        except Exception as exc:
            return failure_result(self.name, dry_run=False, errors=[make_error("send", "EMAIL_SEND_ERROR", str(exc))])
        return success_result(self.name, message, dry_run=False)
