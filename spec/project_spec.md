# EV Charger Infrastructure & Demand Analysis Specification

## 1. Research Questions

1. **Coverage vs. demand:** Where are chargers per capita/EV/highway entrance insufficient across Lisbon parishes and broader Portuguese municipalities?
2. **Traffic hotspots:** Which grid cells or road segments carry intense trip flows but lack proximate charging capacity?
3. **Socio-economic equity:** Do lower-income or lower-EV-adoption neighbourhoods receive fewer chargers relative to population density?
4. **Charger characteristics:** Are fast vs. normal chargers aligned with observed utilisation and demand patterns? Which stations are over/under-used versus capacity?
5. **Data quality:** What gaps, inconsistencies, and duplicates exist across charger datasets, and how do they affect downstream conclusions?

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

### 2.5 Lisbon Mobility & Road Context Datasets (Lisboa Aberta)

| Dataset                                           | Landing Page                                                                                                                                                    | Relevance / Notes                                                                                                                                                                                                           |
| ------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Condicionamentos de Trânsito (ativos e previstos) | https://lisboaaberta.cm-lisboa.pt/index.php/pt/dados/conjuntos-de-dados/item/82-condicionamentos-de-trânsito-ativos-e-previstos-na-cidade-de-Lisboa             | Live/near-term road works & closures; useful to contextualise temporary charger access constraints or explain anomalous traffic counts. Expect frequent updates and polygonal/line geometries describing affected segments. |
| Condicionamentos de Trânsito (histórico)          | https://lisboaaberta.cm-lisboa.pt/index.php/pt/dados/conjuntos-de-dados/item/83-condicionamentos-de-trânsito-histórico                                          | Historical log of closures enables time-series correlation between infrastructure work and charger utilisation or mobility demand. Watch for large file sizes and date-range filters to keep downloads manageable.          |
| Áreas reguladas de estacionamento na via pública  | https://lisboaaberta.cm-lisboa.pt/index.php/pt/dados/conjuntos-de-dados/item/91-áreas-reguladas-de-estacionamento-na-via-pública                               | Spatial polygons of regulated parking zones (EMEL). Supports analysing charger coverage vs. paid-parking supply and identifying resident-priority areas lacking chargers. Requires harmonising zone IDs with parish codes.  |
| Declive Longitudinal da Rede Viária               | https://lisboaaberta.cm-lisboa.pt/index.php/pt/dados/conjuntos-de-dados/item/97-declive-longitudinal-da-rede-viária                                             | Road-network slope attributes (percent grade). Useful when assessing energy consumption patterns or siting fast chargers on steep corridors. Geometry-heavy; ensure CRS alignment with charger points.                      |
| Indicadores de Tráfego                            | https://lisboaaberta.cm-lisboa.pt/index.php/pt/dados/conjuntos-de-dados/item/50-22-indicadores-de-tráfego                                                       | Aggregated traffic indicators (counts, speeds) across monitored segments. Primary candidate for demand-side integration when World Data League/xMap data are unavailable. Validate temporal coverage and sensor metadata.   |

These datasets can be ingested via the dados.cm-lisboa.pt API (often CKAN-based) and profiled like other sources. Prioritise the traffic indicators dataset for core demand analysis, while the others enrich contextual narratives (e.g., closures explaining gaps, parking policy overlaps). Track acquisition scripts for each under `scripts/` as the scope expands. Population-density indicators from INE complement these spatial layers for per-capita metrics.

## 3. Integrated Data Model

```
Entity: Charger
  - station_id (PK)
  - source (lisboa_mobie | e_redes)
  - station_name
  - station_type (fast/normal)
  - sockets_total
  - power_kw
  - usage_type (public/private)
  - latitude, longitude (WGS84)
  - municipality_code (DICOFRE)
  - parish_code (DICOFRE)
  - traffic_grid_id (FK optional)
  - install_date

Entity: Area
  - area_id (parish or municipality code, PK)
  - name
  - population
  - households
  - ev_count (if available)
  - geometry (MultiPolygon)

Entity: TrafficGrid
  - grid_id (PK)
  - centroid_lat/lon
  - geometry_polygon
  - timestamp
  - devices_in
  - devices_out
  - vehicles (if road counter data added)

Relationships:
- Charger -> Area: many-to-one via spatial join (charger point within area polygon).
- Charger -> TrafficGrid: optional many-to-one by assigning to nearest grid cell centroid (<=50 m).
- Area -> TrafficGrid: aggregate traffic metrics per area for demand comparison.

Transformations Needed:
- Parse coordinates from geometry to floats.
- Map municipality/parish names to official codes via lookup table (INE DICOFRE).
- Expand timestamps to timezone-aware (Europe/Lisbon) ISO-8601 strings.
- Normalise charger types (fast/normal) based on IDTIPO or power thresholds.
- Derive coverage metrics: chargers per 10k residents, sockets per EV, fast-charger ratio.

## 4. Extraction & Integration Pipeline
1. **Download**
   - Use `requests`/`aiohttp` to paginate ArcGIS FeatureServer and Opendatasoft endpoints; cache raw JSON/GeoJSON under `data/raw/<source>/`.
   - Store mobility CSV/Parquet in `data/raw/mobility/` (manual download if necessary due to licensing).
2. **Load**
   - Use `geopandas.read_file` for GeoJSON; `pandas.read_json`/`read_csv` for other sources.
   - Convert CRS to EPSG:4326 for consistency.
3. **Clean**
   - Trim whitespace, lowercase textual keys, remove accents using `unidecode` for matching.
   - Parse numeric columns (`TOMADAS`, `potencia_instalada`) to integers/floats.
   - Standardise categorical codes using mapping dictionaries.
   - Handle missing coordinates by dropping records lacking geometry or geocoding addresses when necessary.
4. **Integrate**
   - Spatial join chargers with official parish polygons (GeoJSON shapefile) to attach `area_id`.
   - Aggregate chargers per area: count, sockets sum, fast-charger count.
   - Join mobility grid metrics via nearest-neighbour spatial index (rtree) and aggregate devices per parish/time.
   - Merge socio-demographic indicators on `area_id` to produce final modelling table.
5. **Outputs**
   - `data/processed/chargers_clean.parquet`
   - `data/processed/area_metrics.parquet`
   - `data/processed/integrated_dataset.parquet`
6. **Documentation**
   - Log every transformation in a YAML/Markdown changelog for reproducibility.

## 5. Attribute Characterisation Plan
For each attribute in `integrated_dataset`:
- **Type classification:** numeric, categorical, boolean, datetime, geometry.
- **Distributions:**
  - Numeric: histograms, boxplots, summary stats (mean, median, std, min/max, quantiles).
  - Categorical: frequency tables, top/bottom counts, unique value counts.
  - Text: length stats, presence of special characters.
  - Datetime: coverage window, periodicity (weekday/hour).
- **Missingness:** compute percentage missing per field; visualise with heatmap (missingno).
- **Outliers:** IQR method or z-score for sockets/power; highlight stations >95th percentile.
- **Documentation:** store profiling outputs in `reports/profiling/` (JSON + HTML).
- **Automated profiling:** run `uv run profile-dataset <path> --format <fmt>` to produce JSON summaries plus YData Profiling HTML reports saved to `reports/profiling/<dataset>_<timestamp>.{json,html}` for each raw source.
- **Interactive inspection:** use `uv run marimo run notebooks/profiling_app.py` to preview datasets, schema, and recently generated profiling links during exploratory sessions.

## 6. Data Quality Strategy
- **Missing sockets/power:** Impute using median of same charger type within municipality; flag records with boolean indicator `is_imputed`.
- **Null municipality/parish names:** Map via spatial overlay; fallback to geocoding address text if coordinates exist but names missing.
- **Inconsistent names/accenting:** Apply `unidecode`, uppercase, and trim to compare; join with authoritative lookup table.
- **Timestamp normalisation:** Convert all mobility timestamps to timezone-aware ISO format (Europe/Lisbon) and align to 15-min bins.
- **Documentation:** Maintain a `data_quality_log.md` capturing each rule, justification, and impacted record counts.

## 7. De-duplication Methodology
1. **Normalise** `station_name`, `address`, `parish` by lowercasing, removing punctuation, collapsing whitespace.
2. **Blocking:** Group candidate duplicates by municipality_code and round coordinates to 4 decimal degrees (~11 m) to reduce comparisons.
3. **Similarity scoring:**
   - String similarity using RapidFuzz ratio on names and addresses.
   - Distance threshold: compute haversine distance; duplicates if <50 m.
   - Attribute agreement: sockets difference <=2 or both null.
4. **Resolution:**
   - If duplicates discovered, keep record with richer attribute completeness (non-null power, sockets) or prefer Lisboa dataset for Lisbon-specific metadata.
   - Merge IDs into canonical `charger_uid`; maintain crosswalk table for source IDs.
5. **Audit:** Log duplicate clusters with similarity scores for manual verification.

## 8. Reporting Plan
- **Format:** 3-page ACM template (primary sections) + annexes.
- **Sections:**
  1. Introduction & research motivation.
  2. Data sources and descriptive statistics (tables/figures for charger counts, socket distributions, traffic summaries).
  3. Integrated data model & ETL overview.
  4. Exploratory findings: attribute distributions, spatial heatmaps, gaps.
  5. Data quality handling & limitations.
  6. Conclusion & next steps.
- **Annexes:** sample rows from raw datasets, intermediate tables, attribute dictionary, hours per team member.
- **Tooling recap:** Document Python libraries, spatial tools, QA scripts.

## 9. Task Tracking & Next Deliverables
- [ ] Implement ETL scripts under `scripts/` (charger ingestion, traffic ingestion, socio-dem join).
- [ ] Build QA notebook for attribute profiling and visualisation (CLI profiling scaffolded via `profile_dataset.py`).
- [ ] Run deduplication routine and capture metrics.
- [ ] Draft ACM report with annexes and publish supporting figures.
```
