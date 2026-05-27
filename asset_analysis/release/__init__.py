def run_release_gate(*args, **kwargs):
    from .gate import run_release_gate as _run_release_gate

    return _run_release_gate(*args, **kwargs)


__all__ = ["run_release_gate"]
