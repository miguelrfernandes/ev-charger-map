# EV Charger Map Research Toolkit

This repository documents the workflow for analysing EV charging infrastructure and demand in Lisbon/Portugal. It provides project context, dataset choices, integration strategy, and supporting scripts/specifications for a decision-support pipeline that highlights where additional chargers are needed.

## Project Goals
- Identify coverage gaps in existing EV charging infrastructure relative to population and mobility demand.
- Correlate charger distribution with socio-economic and traffic indicators.
- Build a reproducible data engineering workflow for integrating charger, demographic, and mobility datasets.

## Key Research Questions
1. **Coverage & gaps:** Which parishes/municipalities have high or low charger availability per capita or per EV?
2. **Traffic demand:** Do areas with intense trip origins/destinations lack charging capacity?
3. **Socio-economics:** How do population density, EV adoption, and income correlate with charger locations? Are communities underserved?
4. **Charger characteristics:** Are chargers under/over-utilised relative to capacity and nearby demand? Are there patterns by charger type?
5. **Data quality:** What issues (missing fields, duplicates, inconsistent geocodes) could affect the analysis, and how will we resolve them?

## Dataset Overview
| Dataset | Provider | Format | Approx Size | Purpose |
| --- | --- | --- | --- | --- |
| Lisboa/Mobi.E charging stations | CM Lisboa ArcGIS FeatureServer | GeoJSON/Feature service | ~1k stations, 15+ attrs | Base layer for Lisbon chargers (location, sockets, usage) |
| E-Redes national charging points | e-redes.opendatasoft.com | CSV/GeoJSON | 35k+ chargers, 20+ attrs | Cross-validate Lisbon layer, extend to national coverage |
| Mobility/traffic flows (World Data League or xMap) | Various | CSV/Parquet | 200m grid counts, time-series | Demand proxy for charging needs |
| (Optional) Socio-demographic indicators | INE or dados.cm-lisboa.pt | CSV | Parish-level population, EV adoption | Normalise charger counts by population/EV adoption |

Detailed attribute descriptions, quality notes, and acquisition scripts live in `spec/project_spec.md`.

## Repository Structure
```
README.md              # Quickstart overview (this file)
spec/project_spec.md   # Detailed research/questions/specification
scripts/               # Future Python notebooks/scripts for ETL + analysis
```

## Workflow Summary
1. **Acquire data:** Use Python (pandas/geopandas) scripts under `scripts/` to pull ArcGIS FeatureServer, Opendatasoft API, and mobility datasets.
2. **Clean & harmonise:** Standardise field names, parse coordinates, normalise municipality codes (DICOFRE), unify timestamps.
3. **Integrate:** Spatial joins map chargers to parishes/traffic grids; aggregate sockets and power metrics per area.
4. **Quality control:** Detect missing/duplicate entities, fill gaps (median sockets, inferred coordinates), flag outliers.
5. **Analysis & reporting:** Produce descriptive stats, charts, and the ACM-format report summarising insights and data quality handling.

## Data Acquisition Scripts
Raw downloads land in `data/raw/<source>/` with timestamped filenames.

- Lisboa/Mobi.E FeatureServer:
  ```bash
  uv run download-arcgis-chargers --verbose
  ```
- E-Redes Opendatasoft dataset:
  ```bash
  uv run download-eredes-chargers --refine municipio=Lisboa
  ```
Use `--help` on each command for additional options (pagination size, filters, custom output paths, etc.).

## Data Profiling
Generate attribute summaries for any downloaded dataset and store them under `reports/profiling/`:
```bash
uv run profile-dataset data/raw/lisboa_mobie/latest.geojson --format geojson --dataset-name lisboa_mobie
```
Key options: `--format {geojson,opendatasoft,csv,json}`, `--max-rows`, and `--output` for a custom report path. Each run captures column types, missingness, distributions, and top values for quick QA.

## Tooling & Dependencies
- Python 3.10+
- [uv](https://docs.astral.sh/uv/latest/) for environment + dependency management
- pandas, geopandas, requests, shapely, pyproj
- fuzzywuzzy (or rapidfuzz) for deduplication heuristics
- matplotlib/seaborn for plots

Set up the environment with uv (installs dependencies from `pyproject.toml` and exposes console scripts):
```bash
uv venv
source .venv/bin/activate  # or .venv\\Scripts\\activate on Windows
uv pip install -e .
```
Run the downloaders without activating the environment by prefixing with `uv run`, e.g.:
```bash
uv run download-arcgis-chargers --verbose
```

## Next Steps
- Populate `scripts/` with ETL notebooks/scripts per dataset.
- Implement attribute profiling & QA dashboards.
- Draft the ACM-format report summarising research questions, datasets, and findings.
