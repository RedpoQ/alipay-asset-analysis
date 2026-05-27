from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass
class RuleReason:
    rule: str
    level: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)
