#!/usr/bin/env python3
"""Profile EV charger datasets to capture attribute types, missingness, and distributions."""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple, TYPE_CHECKING

try:
    from scripts.utils import (
        atomic_write_json,
        profiling_output_path,
    )
except ModuleNotFoundError:  # pragma: no cover
    sys.path.append(str(Path(__file__).resolve().parent))
    from utils import (  # type: ignore
        atomic_write_json,
        profiling_output_path,
    )

if TYPE_CHECKING:  # pragma: no cover
    import pandas as pd

_PD = None
_PTYPES = None

LOGGER = logging.getLogger(__name__)
SUPPORTED_FORMATS = {"geojson", "opendatasoft", "csv", "json"}


def ensure_pandas() -> Tuple[Any, Any]:
    global _PD, _PTYPES
    if _PD is None or _PTYPES is None:
        try:
            import pandas as pd  # type: ignore
            from pandas.api import types as ptypes  # type: ignore
        except ModuleNotFoundError as exc:  # pragma: no cover
            raise SystemExit("pandas is required. Run `uv pip install -e .`.") from exc
        _PD = pd
        _PTYPES = ptypes
    return _PD, _PTYPES


def load_records(path: Path, fmt: str):
    pd, _ = ensure_pandas()
    fmt = fmt.lower()
    if fmt not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported format '{fmt}'.")

    if fmt == "csv":
        return pd.read_csv(path)

    with path.open("r", encoding="utf-8") as fp:
        payload = json.load(fp)

    if fmt == "geojson":
        features = payload.get("features", [])
        rows: List[Dict[str, Any]] = []
        for feature in features:
            props = feature.get("properties", {}) or {}
            geometry = feature.get("geometry") or {}
            geom_type = geometry.get("type")
            coords = geometry.get("coordinates")
            if geom_type == "Point" and isinstance(coords, (list, tuple)) and len(coords) >= 2:
                props.setdefault("longitude", coords[0])
                props.setdefault("latitude", coords[1])
            rows.append(props)
        return pd.DataFrame(rows)

    if fmt == "opendatasoft":
        records = payload.get("records", [])
        rows = []
        for record in records:
            fields = record.get("fields", {}) or {}
            fields.setdefault("recordid", record.get("recordid"))
            rows.append(fields)
        return pd.DataFrame(rows)

    if isinstance(payload, list):
        return pd.DataFrame(payload)
    if isinstance(payload, dict):
        return pd.json_normalize(payload)

    raise ValueError("Unable to build DataFrame from JSON payload.")


def column_summary(series):
    pd, ptypes = ensure_pandas()
    non_null = series.notna().sum()
    total = len(series)
    dtype = str(series.dtype)
    summary: Dict[str, Any] = {
        "dtype": dtype,
        "non_null": int(non_null),
        "missing_pct": float(round((total - non_null) / total * 100, 3)) if total else 0.0,
        "unique": int(series.nunique(dropna=True)),
    }

    if total == 0:
        return summary

    if ptypes.is_numeric_dtype(series):
        numeric = pd.to_numeric(series, errors="coerce")
        summary["stats"] = {
            "min": numeric.min(skipna=True),
            "max": numeric.max(skipna=True),
            "mean": numeric.mean(skipna=True),
            "median": numeric.median(skipna=True),
            "std": numeric.std(skipna=True),
        }
    elif ptypes.is_datetime64_any_dtype(series):
        summary["stats"] = {
            "min": series.min(skipna=True).isoformat() if non_null else None,
            "max": series.max(skipna=True).isoformat() if non_null else None,
        }
    elif ptypes.is_bool_dtype(series):
        counts = series.value_counts(dropna=True).to_dict()
        summary["value_counts"] = counts
    else:
        sample_lengths = series.dropna().astype(str).map(len)
        if not sample_lengths.empty:
            summary["text_length"] = {
                "min": int(sample_lengths.min()),
                "max": int(sample_lengths.max()),
                "mean": float(sample_lengths.mean()),
            }

    top_values = series.value_counts(dropna=True).head(5)
    summary["top_values"] = top_values.to_dict()
    return summary


def profile_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
    profile = {
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
        "columns": {},
    }
    for column in df.columns:
        profile["columns"][column] = column_summary(df[column])
    return profile


def infer_format(path: Path, user_format: str | None) -> str:
    if user_format:
        return user_format
    suffix = path.suffix.lower()
    if suffix in {".csv"}:
        return "csv"
    if suffix in {".geojson"}:
        return "geojson"
    return "json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Path to dataset (GeoJSON/JSON/CSV).")
    parser.add_argument(
        "--format",
        choices=sorted(SUPPORTED_FORMATS),
        default=None,
        help="File format override. Auto-detected if omitted.",
    )
    parser.add_argument(
        "--dataset-name",
        default=None,
        help="Name used for output file naming. Defaults to input stem.",
    )
    parser.add_argument(
        "--max-rows",
        type=int,
        default=None,
        help="Optional cap on rows for quick profiling.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Destination path for JSON profile. Defaults to reports/profiling/<dataset>_<timestamp>.json",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)

    dataset_name = args.dataset_name or args.input.stem
    fmt = infer_format(args.input, args.format)
    LOGGER.info("Loading %s as %s", args.input, fmt)

    df = load_records(args.input, fmt)
    LOGGER.info("Loaded %s rows x %s columns before sampling", len(df), len(df.columns))

    if args.max_rows and len(df) > args.max_rows:
        df = df.head(args.max_rows)
        LOGGER.info("Trimmed to %s rows for profiling", len(df))

    profile = profile_dataframe(df)
    profile["source"] = str(args.input)
    profile["dataset_name"] = dataset_name
    profile["format"] = fmt

    output_path = args.output or profiling_output_path(dataset_name)
    atomic_write_json(output_path, profile)
    LOGGER.info("Saved profile to %s", output_path)

    # also print concise summary for quick inspection
    print(json.dumps({"output": str(output_path), "rows": profile["row_count"], "columns": profile["column_count"]}, indent=2))


if __name__ == "__main__":
    main()
