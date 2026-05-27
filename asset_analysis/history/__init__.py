def build_history_index(*args, **kwargs):
    from .indexer import build_history_index as _build_history_index

    return _build_history_index(*args, **kwargs)


def compare_reports(*args, **kwargs):
    from .compare import compare_reports as _compare_reports

    return _compare_reports(*args, **kwargs)


def build_trend_report(*args, **kwargs):
    from .trend_reporter import build_trend_report as _build_trend_report

    return _build_trend_report(*args, **kwargs)


__all__ = ["build_history_index", "compare_reports", "build_trend_report"]
