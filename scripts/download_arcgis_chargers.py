#!/usr/bin/env python3
"""Download Lisboa/Mobi.E chargers from ArcGIS FeatureServer and store as GeoJSON."""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, Iterable, List

try:  # script can be run as module or standalone file
    from scripts.utils import (
        DATA_RAW_ROOT,
        atomic_write_json,
        build_default_output,
        ensure_directory,
        timestamped_filename,
    )
except ModuleNotFoundError:  # pragma: no cover - fallback for direct execution
    sys.path.append(str(Path(__file__).resolve().parent))
    from utils import (  # type: ignore
        DATA_RAW_ROOT,
        atomic_write_json,
        build_default_output,
        ensure_directory,
        timestamped_filename,
    )

DEFAULT_SERVICE_URL = (
    "https://services.arcgis.com/1dSrzEWVQn5kHHyK/arcgis/rest/services/"
    "POITransportes/FeatureServer/2"
)
DEFAULT_BATCH_SIZE = 1000
LOGGER = logging.getLogger(__name__)


def fetch_features(
    service_url: str,
    batch_size: int = DEFAULT_BATCH_SIZE,
    where_clause: str = "1=1",
    out_fields: str = "*",
    max_records: int | None = None,
    token: str | None = None,
) -> List[Dict]:
    """Iterate through the FeatureServer endpoint and return all features."""
    import requests

    offset = 0
    collected: List[Dict] = []
    query_url = service_url.rstrip("/") + "/query"

    while True:
        params = {
            "f": "json",
            "where": where_clause,
            "outFields": out_fields,
            "resultRecordCount": batch_size,
            "resultOffset": offset,
            "outSR": 4326,
            "returnGeometry": "true",
        }
        if token:
            params["token"] = token

        LOGGER.debug("Requesting offset %s", offset)
        response = requests.get(query_url, params=params, timeout=30)
        response.raise_for_status()
        payload = response.json()

        if "error" in payload:
            raise RuntimeError(payload["error"])

        features = payload.get("features", [])
        if not features:
            break

        collected.extend(features)
        offset += len(features)

        if max_records and len(collected) >= max_records:
            collected = collected[:max_records]
            break

        if len(features) < batch_size:
            break

    return collected


def arcgis_to_geojson(features: Iterable[Dict]) -> Dict:
    geojson_features: List[Dict] = []
    for feature in features:
        geometry = feature.get("geometry") or {}
        attributes = feature.get("attributes") or {}

        if {"x", "y"}.issubset(geometry):
            geom = {
                "type": "Point",
                "coordinates": [geometry["x"], geometry["y"]],
            }
        else:
            geom = None

        geojson_features.append(
            {
                "type": "Feature",
                "geometry": geom,
                "properties": attributes,
            }
        )

    return {"type": "FeatureCollection", "features": geojson_features}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--service-url",
        default=DEFAULT_SERVICE_URL,
        help="ArcGIS FeatureServer layer URL (ending with /FeatureServer/<layer id>).",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help="Number of records to request per query (<=2000 per ArcGIS limits).",
    )
    parser.add_argument(
        "--max-records",
        type=int,
        default=None,
        help="Optional cap on downloaded records for testing.",
    )
    parser.add_argument(
        "--where",
        default="1=1",
        help="Optional SQL where clause.",
    )
    parser.add_argument(
        "--out-fields",
        default="*",
        help="Comma-separated list of fields to fetch.",
    )
    parser.add_argument(
        "--token",
        default=None,
        help="ArcGIS token if the service is secured.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Destination GeoJSON path. Defaults to data/raw/lisboa_mobie/<timestamp>.geojson",
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Store raw ArcGIS JSON instead of GeoJSON FeatureCollection.",
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

    features = fetch_features(
        service_url=args.service_url,
        batch_size=args.batch_size,
        where_clause=args.where,
        out_fields=args.out_fields,
        max_records=args.max_records,
        token=args.token,
    )
    LOGGER.info("Fetched %s features", len(features))

    output_dir = ensure_directory(DATA_RAW_ROOT / "lisboa_mobie")
    filename = args.output or build_default_output(
        output_dir,
        timestamped_filename("lisboa_mobie_chargers", "geojson" if not args.raw else "json"),
    )

    if not isinstance(filename, Path):
        filename = Path(filename)

    if args.raw:
        payload = {"features": features}
    else:
        payload = arcgis_to_geojson(features)

    atomic_write_json(filename, payload)
    LOGGER.info("Saved output to %s", filename)


if __name__ == "__main__":
    main()
