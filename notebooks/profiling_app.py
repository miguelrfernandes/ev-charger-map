"""Marimo dashboard for interactive EV charger dataset profiling."""
from __future__ import annotations

from pathlib import Path
from typing import Tuple

import marimo as mo
import pandas as pd

try:
    from scripts.profile_dataset import load_records, infer_format
except ModuleNotFoundError:  # pragma: no cover
    import sys as _sys

    _sys.path.append(str(Path(__file__).resolve().parents[1]))
    from scripts.profile_dataset import load_records, infer_format  # type: ignore

DATA_RAW_ROOT = Path("data/raw")
PROFILE_DIR = Path("reports/profiling")


def _list_datasets() -> list[Tuple[str, str]]:
    """Return (label, path) pairs for available raw datasets."""
    if not DATA_RAW_ROOT.exists():
        return []
    candidates: list[Tuple[str, str]] = []
    for path in DATA_RAW_ROOT.rglob("*"):
        if path.is_file() and path.suffix.lower() in {".json", ".geojson", ".csv"}:
            rel = path.relative_to(DATA_RAW_ROOT)
            label = f"{rel}"
            candidates.append((label, str(path)))
    candidates.sort()
    return candidates


def _load_df(path: Path, fmt: str | None = None) -> pd.DataFrame:
    fmt = infer_format(path, fmt)
    return load_records(path, fmt)


def _latest_profiles() -> list[str]:
    if not PROFILE_DIR.exists():
        return []
    return sorted(str(p) for p in PROFILE_DIR.glob("*.html"))


@mo.app()
def app() -> mo.ui.column:
    dataset_options = _list_datasets()
    if dataset_options:
        default_value = dataset_options[0][1]
    else:
        default_value = ""

    dataset_select = mo.ui.dropdown(
        dataset_options,
        value=default_value,
        label="Choose raw dataset file",
        allow_select_none=not dataset_options,
    )

    format_select = mo.ui.radio(
        options=[("auto", "auto"), ("geojson", "geojson"), ("opendatasoft", "opendatasoft"), ("csv", "csv"), ("json", "json")],
        value="auto",
        label="Format override",
    )

    preview_rows = mo.ui.slider(
        start=5,
        stop=50,
        step=5,
        value=10,
        label="Preview rows",
    )

    @mo.cell
    def _header():
        return mo.md("""
        # EV Charger Profiling (Marimo)
        Use the controls below to load any raw dataset (ArcGIS, Opendatasoft, CSV/GeoJSON) and preview basic statistics.
        """)

    @mo.cell
    def _dataset_info():
        if not dataset_options:
            return mo.md("> ⚠️ No files under `data/raw/`. Run a downloader first.")
        selected = dataset_select.value
        fmt_override = format_select.value
        fmt = None if fmt_override == "auto" else fmt_override
        df = _load_df(Path(selected), fmt)
        info = mo.md(
            f"**File:** `{selected}`  \\n**Rows:** {len(df):,} — **Columns:** {len(df.columns)}"
        )
        table = mo.ui.table(df.head(preview_rows.value))
        stats = df.describe(include="all", datetime_is_numeric=True).fillna("")
        stats_table = mo.ui.table(stats)
        schema_md = mo.md("\n".join(f"- `{col}`" for col in df.columns))
        return mo.vstack([
            info,
            mo.hstack([dataset_select, format_select, preview_rows]),
            mo.ui.accordion({
                "Schema": schema_md,
                "Preview": table,
                "Summary stats": stats_table,
            }, value="Preview"),
        ])

    @mo.cell
    def _profiles_panel():
        items = _latest_profiles()
        if not items:
            return mo.md("> ℹ️ No YData HTML reports yet. Run `profile-dataset` to create one.")
        links = "\n".join(f"- [{Path(p).name}]({p})" for p in items[-10:])
        return mo.md(f"## Recent profiling reports\n{links}")

    return mo.vstack([
        _header,
        dataset_select,
        format_select,
        preview_rows,
        _dataset_info,
        _profiles_panel,
    ])


def main() -> None:
    mo.run()


if __name__ == "__main__":
    main()
