from __future__ import annotations


SIGNAL_LABELS = {
    "add": "可补仓观察",
    "reduce": "建议减仓观察",
    "hold": "继续持有观察",
}


def localize_signal_label(signal: str) -> str:
    return SIGNAL_LABELS.get(str(signal).lower(), str(signal) or "继续观察")
