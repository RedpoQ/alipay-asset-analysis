from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from asset_analysis.ux.paths import find_project_root


def main() -> int:
    project_root = find_project_root(Path(__file__).resolve())
    setup_code = subprocess.call(
        [sys.executable, "-m", "asset_analysis.ux.setup_check", "--config", "private/config.local.yaml"],
        cwd=project_root,
    )
    if setup_code != 0:
        print("Init command: python -m asset_analysis.onboarding.init_project", file=sys.stderr)
        return setup_code
    return subprocess.call(
        [sys.executable, "-m", "asset_analysis.workflow.daily_run", "--config", "private/config.local.yaml"],
        cwd=project_root,
    )


if __name__ == "__main__":
    raise SystemExit(main())
