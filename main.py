"""Repository-root launcher for FloorPlanner.

Allows running `python main.py` without installing the package first.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def run() -> int:
    """Run the application from repository root without installation."""
    from app.main import main

    return main()


if __name__ == "__main__":
    raise SystemExit(run())
