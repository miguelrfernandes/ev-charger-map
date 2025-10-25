"""Shared helpers for ETL scripts."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


DATA_RAW_ROOT = Path("data/raw")
REPORTS_ROOT = Path("reports")


def ensure_directory(path: Path) -> Path:
    """Create directory (and parents) if missing and return it."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def timestamped_filename(prefix: str, suffix: str) -> str:
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    return f"{prefix}_{timestamp}.{suffix}"


def atomic_write_json(path: Path, payload: Any) -> None:
    """Write payload as JSON with a temporary file swap for safety."""
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with tmp_path.open("w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=2)
    tmp_path.replace(path)


def build_default_output(root: Path, filename: str) -> Path:
    ensure_directory(root)
    return root / filename


def profiling_output_path(dataset_name: str, suffix: str = "json") -> Path:
    """Return default profiling output path."""
    profiling_dir = ensure_directory(REPORTS_ROOT / "profiling")
    filename = timestamped_filename(dataset_name, suffix)
    return profiling_dir / filename
