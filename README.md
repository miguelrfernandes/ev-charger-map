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

## Other Resources to Explore

| Dataset                                           | Landing Page                                                                                                                                        | Relevance / Notes                                                                                                                                                                                                           |
| ------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Condicionamentos de Trânsito (ativos e previstos) | https://lisboaaberta.cm-lisboa.pt/index.php/pt/dados/conjuntos-de-dados/item/82-condicionamentos-de-trânsito-ativos-e-previstos-na-cidade-de-Lisboa | Live/near-term road works & closures; useful to contextualise temporary charger access constraints or explain anomalous traffic counts. Expect frequent updates and polygonal/line geometries describing affected segments. |
| Condicionamentos de Trânsito (histórico)          | https://lisboaaberta.cm-lisboa.pt/index.php/pt/dados/conjuntos-de-dados/item/83-condicionamentos-de-trânsito-histórico                              | Historical log of closures enables time-series correlation between infrastructure work and charger utilisation or mobility demand. Watch for large file sizes and date-range filters to keep downloads manageable.          |
| Áreas reguladas de estacionamento na via pública  | https://lisboaaberta.cm-lisboa.pt/index.php/pt/dados/conjuntos-de-dados/item/91-áreas-reguladas-de-estacionamento-na-via-pública                    | Spatial polygons of regulated parking zones (EMEL). Supports analysing charger coverage vs. paid-parking supply and identifying resident-priority areas lacking chargers. Requires harmonising zone IDs with parish codes.  |
| Declive Longitudinal da Rede Viária               | https://lisboaaberta.cm-lisboa.pt/index.php/pt/dados/conjuntos-de-dados/item/97-declive-longitudinal-da-rede-viária                                 | Road-network slope attributes (percent grade). Useful when assessing energy consumption patterns or siting fast chargers on steep corridors. Geometry-heavy; ensure CRS alignment with charger points.                      |
| Indicadores de Tráfego                            | https://lisboaaberta.cm-lisboa.pt/index.php/pt/dados/conjuntos-de-dados/item/50-22-indicadores-de-tráfego                                           | Aggregated traffic indicators (counts, speeds) across monitored segments. Primary candidate for demand-side integration when World Data League/xMap data are unavailable. Validate temporal coverage and sensor metadata.   |

## 2. Dataset Selection & Description

### 2.1 Lisboa / Mobi.E Charging Stations (ArcGIS FeatureServer)

- **Endpoint:** `https://services.arcgis.com/1dSrzEWVQn5kHHyK/arcgis/rest/services/POITransportes/FeatureServer/2`
- **Format:** GeoJSON via ArcGIS REST (structured, spatial)
- **Size:** ~160 features (layer dedicated to Lisboa Mobi.E stations inside POITransportes service with ObjectID, COD_SIG, DESCRICAO, MORADA, TOMADAS, IDTIPO, geometry)
- **Key attributes:** station code, station name, address, number of sockets, usage type (public/private), charger type, latitude/longitude geometry.
- **Missing/incomplete:** Some records lack socket counts or have null addresses; coordinate precision varies.
- **Quality concerns:** Inconsistent casing/accents in `MORADA`/`FREGUESIA`, station types encoded as numeric codes, potential duplicates with national dataset.

### 2.2 E-Redes National Charging Points (Opendatasoft)

- **Endpoint:** `https://e-redes.opendatasoft.com/api/records/1.0/search/?dataset=postos_carregamento_ves&rows=5000&start=`
- **Format:** JSON/CSV (tabular, spatial fields `geo_point_2d`, `geo_shape`)
- **Size:** ~35,849 records, ~25 columns (district, municipality, parish, power, connectors).
- **Key attributes:** `id`, `designacao`, `municipio`, `freguesia`, `potencia_instalada`, `n_pontos_carregamento`, `estado`, `data_instalacao`.
- **Missing/incomplete:** Some rows lack `potencia_instalada` or `geo_point_2d`; parish names sometimes blank.
- **Quality concerns:** Text accents vs. ASCII, municipality naming mismatches with Lisbon dataset, duplicates near same coordinates with slight name variations.

### 2.3 Mobility / Traffic Flows (World Data League Lisbon Challenge)

- **Format:** CSV/Parquet per 15-min interval grid (200 m x 200 m)
- **Size:** Tens of millions of rows; columns include `grid_id`, `timestamp`, `devices_in`, `devices_out`.
- **Key attributes:** grid cell geometry, counts of entering/exiting devices, aggregated device IDs.
- **Missing/incomplete:** Some intervals missing counts; timestamps in UTC; grid metadata required for spatial join.
- **Quality concerns:** Need to respect privacy aggregation; ensure consistent CRS when mapping to parishes.

### 2.4 Optional Socio-Demographic Indicators (INE/Dados CM Lisboa)

- **Format:** CSV (parish-level population, EV ownership, income proxies)
- **Usage:** Provide denominators for per-capita metrics and equity analysis.

### 2.6 Population Density (INE via dados.gov.pt)

- **Landing page:** https://dados.gov.pt/pt/datasets/densidade-populacional-n-o-km2-7/
- **API resource:** `https://www.ine.pt/ine/json_indicador/pindica.jsp?op=2&varcd=0012280&lang=PT`
- **Format:** JSON indicator series (nested arrays with NUTS 2024 codes, sex, value, year)
- **Size:** National coverage with breakdown by sex and territorial unit (NUTS I/II/III); each request returns dozens of records per region/sex/time slice.
- **Key attributes:** `geodsg` (territorial description), `geocod` (NUTS code), `Sexo`, `Valor`, `Anos`, indicator metadata.
- **Usage:** Normalise charger counts per km² or per resident by joining NUTS regions to municipalities/parishes; feed population density into gap analysis and equity scoring.
- **Missing/incomplete:** Some indicators may contain placeholder values (e.g., `"Valor": "x"` for suppressed data) or aggregated codes lacking finer geography; requires filtering to desired geography (NUTS III covering Lisboa Metropolitana) and casting string numerics to floats.
- **Quality concerns:** JSON arrays embed metadata headers followed by observations; need parsing helpers. Ensure up-to-date NUTS codes align with DICOFRE lookups before joins.
