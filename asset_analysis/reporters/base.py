from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass


@dataclass
class ReporterOutput:
    mode: str
    used: str
    provider: str | None = None
    model: str | None = None
    error: str | None = None
    report_md: str = ""

    def to_dict(self) -> dict[str, str | None]:
        return asdict(self)


class BaseReporter(ABC):
    name = "base"

    @abstractmethod
    def render(self, result) -> ReporterOutput:
        raise NotImplementedError
