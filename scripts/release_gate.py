from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    project_root = Path(__file__).resolve().parent.parent
    return subprocess.call(
        [sys.executable, "-m", "asset_analysis.release.gate", "--output", "reports/release_gate"],
        cwd=project_root,
    )


if __name__ == "__main__":
    raise SystemExit(main())
