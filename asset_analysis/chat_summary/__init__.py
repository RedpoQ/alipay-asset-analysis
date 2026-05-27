def build_chat_summary(*args, **kwargs):
    from .builder import build_chat_summary as _build_chat_summary

    return _build_chat_summary(*args, **kwargs)


def format_chat_summary(*args, **kwargs):
    from .formatter import format_chat_summary as _format_chat_summary

    return _format_chat_summary(*args, **kwargs)


__all__ = ["build_chat_summary", "format_chat_summary"]
