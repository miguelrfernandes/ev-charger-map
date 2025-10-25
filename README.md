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

| Dataset                                            | Provider                       | Format                  | Approx Size                          | Purpose                                                   |
| -------------------------------------------------- | ------------------------------ | ----------------------- | ------------------------------------ | --------------------------------------------------------- |
| Lisboa/Mobi.E charging stations                    | CM Lisboa ArcGIS FeatureServer | GeoJSON/Feature service | ~160 POIs, 10+ attrs                 | Base layer for Lisbon chargers (location, sockets, usage) |
| E-Redes national charging points                   | e-redes.opendatasoft.com       | JSON/CSV                | 35k+ chargers, 20+ attrs             | Cross-validate Lisbon layer, extend to national coverage  |
| Mobility/traffic flows (World Data League or xMap) | Various                        | CSV/Parquet             | 200m grid counts, time-series        | Demand proxy for charging needs                           |
| Population density indicator                       | INE via dados.gov.pt           | JSON API                | National coverage per NUTS/sex       | Provides per-capita normalisation factors                 |
| (Optional) Socio-demographic indicators            | INE or dados.cm-lisboa.pt      | CSV                     | Parish-level population, EV adoption | Normalise charger counts by population/EV adoption        |

Set up the environment with uv (installs dependencies from `pyproject.toml` and exposes console scripts):

```bash
uv sync
source .venv/bin/activate
marimo edit
```
