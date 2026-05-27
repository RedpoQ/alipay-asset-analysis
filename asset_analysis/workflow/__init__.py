from .config import DailyWorkflowConfig, load_workflow_config


def run_daily_workflow(*args, **kwargs):
    from .daily_run import run_daily_workflow as _run_daily_workflow

    return _run_daily_workflow(*args, **kwargs)


__all__ = ["DailyWorkflowConfig", "load_workflow_config", "run_daily_workflow"]
