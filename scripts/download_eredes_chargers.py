#!/usr/bin/env python3
"""Download E-Redes national EV charger dataset from Opendatasoft API."""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, List

try:
    from scripts.utils import (
        DATA_RAW_ROOT,
        atomic_write_json,
        build_default_output,
        ensure_directory,
        timestamped_filename,
    )
except ModuleNotFoundError:  # pragma: no cover
    sys.path.append(str(Path(__file__).resolve().parent))
    from utils import (  # type: ignore
        DATA_RAW_ROOT,
        atomic_write_json,
        build_default_output,
        ensure_directory,
        timestamped_filename,
    )

DEFAULT_BASE_URL = "https://e-redes.opendatasoft.com/api/records/1.0/search/"
DEFAULT_DATASET = "postos-carregamento-ves"
DEFAULT_PAGE_SIZE = 1000
LOGGER = logging.getLogger(__name__)


def fetch_records(
    base_url: str,
    dataset: str,
    page_size: int = DEFAULT_PAGE_SIZE,
    max_records: int | None = None,
    extra_params: Dict[str, str] | None = None,
) -> List[Dict]:
    import requests

    start = 0
    collected: List[Dict] = []
    params_base = {"dataset": dataset, "rows": page_size}
    if extra_params:
        params_base.update(extra_params)

    while True:
        params = {**params_base, "start": start}
        LOGGER.debug("Requesting start=%s", start)
        response = requests.get(base_url, params=params, timeout=30)
        response.raise_for_status()
        payload = response.json()

        records = payload.get("records", [])
        if not records:
            break

        collected.extend(records)
        start += len(records)

        if max_records and len(collected) >= max_records:
            collected = collected[:max_records]
            break

        if len(records) < page_size:
            break

    return collected


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help="Opendatasoft API endpoint",
    )
    parser.add_argument(
        "--dataset",
        default=DEFAULT_DATASET,
        help="Dataset identifier on the platform",
    )
    parser.add_argument(
        "--page-size",
        type=int,
        default=DEFAULT_PAGE_SIZE,
        help="Records per request (max 1000 for this API).",
    )
    parser.add_argument(
        "--max-records",
        type=int,
        default=None,
        help="Optional limit for testing.",
    )
    parser.add_argument(
        "--refine",
        action="append",
        default=[],
        metavar="FIELD=VALUE",
        help="Optional Opendatasoft refine filter(s). Repeat flag to add more filters.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Destination JSON path. Defaults to data/raw/eredes/<timestamp>.json",
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

    extra_params = {}
    for refine in args.refine:
        if "=" not in refine:
            raise ValueError(f"Invalid refine expression '{refine}'. Use FIELD=VALUE format.")
        field, value = refine.split("=", 1)
        extra_params[f"refine.{field}"] = value

    records = fetch_records(
        base_url=args.base_url,
        dataset=args.dataset,
        page_size=args.page_size,
        max_records=args.max_records,
        extra_params=extra_params or None,
    )
    LOGGER.info("Fetched %s records", len(records))

    output_dir = ensure_directory(DATA_RAW_ROOT / "eredes")
    filename = args.output or build_default_output(
        output_dir,
        timestamped_filename("eredes_chargers", "json"),
    )

    if not isinstance(filename, Path):
        filename = Path(filename)

    payload = {
        "dataset": args.dataset,
        "count": len(records),
        "records": records,
    }
    atomic_write_json(filename, payload)
    LOGGER.info("Saved output to %s", filename)


if __name__ == "__main__":
    main()
