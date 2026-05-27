from __future__ import annotations

from .base import BaseNotifier, success_result


class DryRunNotifier(BaseNotifier):
    name = "dry_run"
    dry_run = True

    def send(self, message: dict) -> dict:
        return success_result(self.name, message, dry_run=True)
