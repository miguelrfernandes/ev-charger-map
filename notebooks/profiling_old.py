from __future__ import annotations

import argparse
import json
import logging
import sys
import traceback
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Dict, List, Tuple, TYPE_CHECKING

import marimo

try:
    from scripts.utils import atomic_write_json, profiling_output_path
except ModuleNotFoundError:  # pragma: no cover
    REPO_ROOT = Path(__file__).resolve().parents[1]
    sys.path.append(str(REPO_ROOT))
    from scripts.utils import atomic_write_json, profiling_output_path  # type: ignore

if TYPE_CHECKING:  # pragma: no cover
    import pandas as pd

logging.basicConfig(level=logging.INFO)

_PD = None
_PTYPES = None

LOGGER = logging.getLogger(__name__)
SUPPORTED_FORMATS = {"geojson", "opendatasoft", "csv", "json", "parquet"}


def make_json_safe(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {k: make_json_safe(v) for k, v in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [make_json_safe(v) for v in value]
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:
            pass
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass
    return value


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
    if fmt == "parquet":
        return pd.read_parquet(path)

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
        summary["value_counts"] = series.value_counts(dropna=True).to_dict()
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


def profile_dataframe(df) -> Dict[str, Any]:
    profile = {
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
        "columns": {},
    }
    for column in df.columns:
        profile["columns"][column] = column_summary(df[column])
    return profile


def generate_ydata_report(df, dataset_name: str, output_path: Path | None, mode: str) -> Path | None:
    pd, _ = ensure_pandas()
    try:
        from ydata_profiling import ProfileReport
    except ModuleNotFoundError as exc:  # pragma: no cover
        LOGGER.warning("Skipping YData Profiling export because dependency is missing: %s", exc)
        return None

    minimal = mode == "minimal"
    title = f"{dataset_name} profile ({mode})"
    report = ProfileReport(df, title=title, minimal=minimal)
    output_path = output_path or profiling_output_path(dataset_name, "html")
    report.to_file(output_path)
    return output_path


def infer_format(path: Path, user_format: str | None) -> str:
    if user_format:
        return user_format
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return "csv"
    if suffix == ".geojson":
        return "geojson"
    if suffix in {".parquet", ".pq"}:
        return "parquet"
    return "json"


def profile_dataset(
    input_path: Path,
    *,
    fmt: str | None = None,
    dataset_name: str | None = None,
    max_rows: int | None = None,
    output: Path | None = None,
    skip_ydata: bool = False,
    ydata_html: Path | None = None,
    ydata_mode: str = "minimal",
    verbose: bool = False,
) -> Dict[str, Any]:
    LOGGER.setLevel(logging.DEBUG if verbose else logging.INFO)
    dataset_name = dataset_name or input_path.stem
    fmt = infer_format(input_path, fmt)
    LOGGER.info("Loading %s as %s", input_path, fmt)

    df = load_records(input_path, fmt)
    LOGGER.info("Loaded %s rows x %s columns before sampling", len(df), len(df.columns))

    if max_rows and len(df) > max_rows:
        df = df.head(max_rows)
        LOGGER.info("Trimmed to %s rows for profiling", len(df))

    profile = profile_dataframe(df)
    profile["source"] = str(input_path)
    profile["dataset_name"] = dataset_name
    profile["format"] = fmt

    output_path = output or profiling_output_path(dataset_name)
    atomic_write_json(output_path, make_json_safe(profile))
    LOGGER.info("Saved profile to %s", output_path)

    ydata_path = None
    if not skip_ydata:
        ydata_path = generate_ydata_report(df, dataset_name, ydata_html, ydata_mode)
        if ydata_path:
            LOGGER.info("Saved YData Profiling report to %s", ydata_path)

    summary = {
        "output": str(output_path),
        "rows": profile["row_count"],
        "columns": profile["column_count"],
    }
    if ydata_path:
        summary["ydata_html"] = str(ydata_path)

    return {
        "profile": profile,
        "summary": summary,
        "output_path": output_path,
        "ydata_path": ydata_path,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Path to dataset (GeoJSON/JSON/CSV/Parquet).")
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
        "--skip-ydata",
        action="store_true",
        help="Disable YData Profiling HTML export.",
    )
    parser.add_argument(
        "--ydata-html",
        type=Path,
        default=None,
        help="Custom output path for YData Profiling HTML report (default: reports/profiling/<dataset>_<timestamp>.html).",
    )
    parser.add_argument(
        "--ydata-mode",
        choices=["minimal", "explorative"],
        default="minimal",
        help="Profiling configuration for YData reports (default: minimal).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = profile_dataset(
        input_path=args.input,
        fmt=args.format,
        dataset_name=args.dataset_name,
        max_rows=args.max_rows,
        output=args.output,
        skip_ydata=args.skip_ydata,
        ydata_html=args.ydata_html,
        ydata_mode=args.ydata_mode,
        verbose=args.verbose,
    )
    print(json.dumps(result["summary"], indent=2))


__generated_with = "0.7.20"
app = marimo.App(width="medium")


@app.cell
def __():
    import marimo as mo

    return (mo,)


@app.cell
def __(mo):
    return mo.md(
        r"""
        # Dataset profiling

        Provide a dataset path, tweak optional parameters, and click **Profile dataset** to
        generate JSON and (optionally) YData HTML summaries. The CLI entrypoint now lives in
        this notebook (`notebooks/profiling.py`) and can still be invoked via `scripts/profile_dataset.py`.
        """
    )


@app.cell
def __():
    return profile_dataset, SUPPORTED_FORMATS


@app.cell
def __(SUPPORTED_FORMATS, mo):
    dataset_path = mo.ui.text()
    dataset_name = mo.ui.text()
    format_dropdown = mo.ui.dropdown(["auto", *sorted(SUPPORTED_FORMATS)])
    max_rows = mo.ui.text()
    output_path = mo.ui.text()
    ydata_switch = mo.ui.switch()
    ydata_html = mo.ui.text()
    ydata_mode = mo.ui.dropdown(["minimal", "explorative"])
    verbose_switch = mo.ui.switch()
    run_button = mo.ui.run_button(label="Profile dataset")

    controls = mo.vstack(
        [
            mo.md("**Input path**"),
            dataset_path,
            mo.md("**Dataset name (optional)**"),
            dataset_name,
            mo.md("**Format override** (auto = infer)"),
            format_dropdown,
            mo.md("**Max rows** (blank = full dataset)"),
            max_rows,
            mo.md("**JSON output path** (optional)"),
            output_path,
            mo.md("**Generate YData HTML report**"),
            ydata_switch,
            mo.md("**YData HTML path** (optional)"),
            ydata_html,
            mo.md("**YData mode**"),
            ydata_mode,
            mo.md("**Verbose logging**"),
            verbose_switch,
            run_button,
        ]
    )
    controls
    return (
        dataset_path,
        dataset_name,
        format_dropdown,
        max_rows,
        output_path,
        ydata_switch,
        ydata_html,
        ydata_mode,
        verbose_switch,
        run_button,
    )


@app.cell
def __(
    dataset_name,
    dataset_path,
    format_dropdown,
    max_rows,
    mo,
    output_path,
    profile_dataset,
    run_button,
    verbose_switch,
    ydata_html,
    ydata_mode,
    ydata_switch,
):
    from pathlib import Path

    profile_result = None
    ui_output = None

    def parse_optional_int(raw: str | None) -> int | None:
        raw = (raw or "").strip()
        if not raw:
            return None
        value = int(raw)
        if value < 1:
            raise ValueError("Value must be positive.")
        return value

    def parse_optional_path(raw: str | None) -> Path | None:
        raw = (raw or "").strip()
        return Path(raw) if raw else None

    if not run_button.value:
        ui_output = mo.md("Configure parameters and click **Profile dataset**.")
    else:
        dataset_text = dataset_path.value.strip()
        if not dataset_text:
            ui_output = mo.md("Provide a valid dataset path.")
        else:
            try:
                max_rows_value = parse_optional_int(max_rows.value)
                fmt_choice = format_dropdown.value
                fmt_arg = None if fmt_choice == "auto" else fmt_choice

                profile_result = profile_dataset(
                    input_path=Path(dataset_text),
                    fmt=fmt_arg,
                    dataset_name=dataset_name.value.strip() or None,
                    max_rows=max_rows_value,
                    output=parse_optional_path(output_path.value),
                    skip_ydata=not ydata_switch.value,
                    ydata_html=parse_optional_path(ydata_html.value),
                    ydata_mode=ydata_mode.value,
                    verbose=bool(verbose_switch.value),
                )

                profile = profile_result["profile"]
                summary = profile_result["summary"]

                ui_output = mo.md(
                    f"""
                    ### Profile summary
                    - **Rows:** {profile['row_count']}
                    - **Columns:** {profile['column_count']}
                    - **JSON output:** `{summary['output']}`
                    {"- **YData HTML:** `{}`".format(summary['ydata_html']) if 'ydata_html' in summary else ""}
                    """
                )
            except ValueError as exc:
                ui_output = mo.md(f"**Invalid max rows:** {exc}")
            except Exception as exc:  # pragma: no cover - interactive feedback
                ui_output = mo.md(f"**Error:** {exc}")
                traceback.print_exc()
    
    ui_output
    return (profile_result,)


@app.cell
def __(mo, profile_result):
    table = None
    if profile_result:
        columns = profile_result["profile"]["columns"]
        rows = []
        for name, stats in columns.items():
            rows.append(
                {
                    "column": name,
                    "dtype": stats.get("dtype"),
                    "non_null": stats.get("non_null"),
                    "missing_pct": stats.get("missing_pct"),
                    "unique": stats.get("unique"),
                }
            )
        table = mo.ui.table(rows, max_height=360, pagination=False)
    return table


if __name__ == "__main__":
    app.run()
