# EV Charging Points - Relation with Population Density and Income

This project identifies the relationship between publicly available EV charging points, personal income, and population density across Portugal's mainland municipalities. We analyze 278 municipalities to answer:

1. Do municipalities with higher population density have more charging points?
2. Are charging points more common in higher income municipalities?
3. Which municipalities should invest more in EV chargers?

**Key Findings:** There is a positive correlation between charging points and both population density and income. Municipalities like Porto, Lisboa, and Oeiras lead in charging infrastructure.

## How to Run

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync
source .venv/bin/activate
marimo edit
```

## Datasets

| Source  | Description                           | Year    | Link                                                                                                             |
| ------- | ------------------------------------- | ------- | ---------------------------------------------------------------------------------------------------------------- |
| INE     | Average income per municipality       | 2023    | [Download](https://www.ine.pt/ngt_server/attachfileu.jsp?look_parentBoui=739291160&att_display=n&att_download=y) |
| INE     | Population density per municipality   | 2024    | [Download](https://dados.gov.pt/pt/datasets/densidade-populacional-n-o-km2-7/)                                   |
| E-REDES | EV charging station connection points | Q3 2025 | [Explore](https://e-redes.opendatasoft.com/explore/dataset/postos_carregamento_ves/information/)                 |

**Note:** Azores and Madeira municipalities are excluded due to incomplete E-REDES data.

## Data Processing

### Income Dataset

- **Source:** INE Excel file with municipality-level gross income
- **Preprocessing:** Extract municipality name and average gross family income
- **Output:** 308 municipalities

### Population Density Dataset

- **Source:** INE CSV with population density (persons/km²)
- **Preprocessing:** Skip metadata rows, filter for 2024, extract municipalities using 7-digit NUTS codes
- **Encoding:** latin-1
- **Output:** 308 municipalities

### Charging Points Dataset

- **Source:** E-REDES with charging stations and points per municipality
- **Preprocessing:**
  - Fix casing issues (e.g., "Castro daire" → "Castro Daire")
  - Fix encoding issues
  - Aggregate by municipality using sum
- **Output:** 278 municipalities (mainland only)

### Integrated Dataset

All datasets merged on municipality name, resulting in 278 records with:

- Municipality name
- Average gross family income
- Population density
- Number of charging stations
- Number of charging points

## Key Findings

### Charging Points vs Population Density

- 6 of top 10 municipalities by charging points are also in top 10 by population density
- Strong positive correlation

### Charging Points vs Income

- 5 of top 10 municipalities by charging points are also in top 10 by income
- Moderate correlation

### Municipalities to Prioritize

**In both income AND density top 30, but NOT in charging points top 30:**

- Entroncamento

**In income top 30 only (14 municipalities):**
Alcochete, Arruda dos Vinhos, Castro Verde, Condeixa-a-Nova, Entroncamento, Figueira da Foz, Guarda, Palmela, Santiago do Cacém, Sesimbra, Sines, Vila Nova da Barquinha, Vila Real, Évora

**In density top 30 only (12 municipalities):**
Entroncamento, Espinho, Moita, Paços de Ferreira, Póvoa de Varzim, São João da Madeira, Trofa, Valongo, Vila do Conde, Vila Nova de Famalicão, Vizela, Ílhavo

## Tools Used

- **Marimo:** Interactive Python notebooks
- **Pandas:** Data manipulation
- **ydata_profiling:** Automated data profiling
- **Matplotlib:** Data visualization
- **Claude.ai:** Code generation assistance

## Limitations

1. Datasets from different years (2023-2025)
2. E-REDES data excludes Azores and Madeira
3. Analysis uses absolute charging point counts (not normalized by area or population)
4. INE data formatting is not machine-friendly (Excel layouts, latin-1 encoding, inconsistent municipality identifiers)

## Future Work

- Normalize metrics (e.g., charging points per km² or per household)
- Investigate correlation between income and EV adoption rates
- Include temporal analysis as newer data becomes available
