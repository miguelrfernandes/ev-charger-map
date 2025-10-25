#!/usr/bin/env python3
"""CLI shim that delegates dataset profiling to the marimo notebook module."""
from __future__ import annotations

import sys
from pathlib import Path

try:
    from notebooks.profiling import main
except ModuleNotFoundError:  # pragma: no cover
    REPO_ROOT = Path(__file__).resolve().parents[1]
    sys.path.append(str(REPO_ROOT))
    from notebooks.profiling import main  # type: ignore


if __name__ == "__main__":
    main()
