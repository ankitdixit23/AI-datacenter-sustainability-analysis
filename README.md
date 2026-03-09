# AI Data Center Sustainability Analysis

**Spatial analysis of U.S. AI data center locations, grid carbon intensity, and regional water stress to evaluate sustainable siting policy.**

> UChicago Harris School — **DAP II (30538) Final Project**, Winter 2026  
> **Authors:** Manav Mutneja (`manavm-afk`) · Ankit Dixit (`ankitdixit23`)

---

# Research Question

**How do the locations of AI/cloud data centers in the United States relate to local carbon intensity of the electricity grid and regional water stress — and what are the policy implications for sustainable data center siting?**

## Sub-Questions

1. Which U.S. counties have the highest concentration of data centers, and how carbon-intensive is their local electricity grid?
2. Are data centers disproportionately located in water-stressed regions?
3. Under projected growth scenarios, how might future data center siting exacerbate or alleviate grid carbon and water stress?

---

# Streamlit Dashboard

🔗 **Live Dashboard**  
https://ai-datacenter-sustainability.streamlit.app

> **Note:** The Streamlit Community Cloud app may take **30–60 seconds to wake up** if it has been idle.

The interactive dashboard allows users to:

- Explore a **map of data center locations** colored by carbon intensity or water stress
- Compare **states by carbon intensity vs. data center concentration**
- View **future water stress projections (2030–2080)** under BAU, Optimistic, and Pessimistic scenarios
- Filter by **state, CO₂ rate range, and water stress category**

---

# Setup

### Option A — Conda (recommended)

```bash
conda env create -f environment.yml
conda activate dc_sustainability
```

### Option B — pip

```bash
pip install -r requirements.txt
```

---

# Project Structure

```
├── README.md
├── requirements.txt
├── environment.yml
├── .gitignore
├── final_project.qmd
├── final_project_analysis.qmd
├── final_project.html
├── final_project.pdf
│
├── code/
│   ├── download_data.py
│   ├── preprocessing.py
│   └── generate_charts.py
│
├── data/
│   ├── raw-data/
│   │   ├── im3_open_source_data_center_atlas_v2026.02.09.csv
│   │   ├── egrid2023_data_rev2.xlsx
│   │   ├── Aqueduct40_baseline_monthly_y2023m07d05.csv
│   │   └── Aqueduct40_future_annual_y2023m07d05.csv
│   │
│   └── derived-data/
│       ├── datacenters_master.csv
│       ├── datacenters_with_emissions.csv
│       ├── datacenters_with_water_stress.csv
│       ├── county_summary.csv
│       ├── state_summary.csv
│       ├── aqueduct_annual_summary.csv
│       ├── aqueduct_future_water_stress_na.csv
│       └── water_stress_county_summary.csv
│
├── output_charts/
│   ├── fig1_top_states.png
│   ├── fig2a_us_map_states.png
│   ├── fig2b_us_map_counties.png
│   ├── fig3_egrid_subregions.png
│   ├── fig4_water_stress.png
│   └── fig5_dual_risk_scatter.png
│
└── streamlit-app/
    ├── app.py
    ├── requirements.txt
    ├── datacenters_master.csv
    ├── state_summary.csv
    ├── county_summary.csv
    ├── datacenters_with_water_stress.csv
    └── aqueduct_future_water_stress_na.csv
```

---

# Data Sources

| Dataset | Source | Format | Granularity |
|--------|--------|--------|-------------|
| **IM3 Open Source Data Center Atlas** | Pacific Northwest National Laboratory (PNNL / DOE) | CSV | Facility-level |
| **EPA eGRID 2023** | U.S. Environmental Protection Agency | XLSX | Plant / grid subregion |
| **WRI Aqueduct 4.0** | World Resources Institute | CSV | HydroSHEDS catchment |

### Source Links

IM3 Atlas  
https://data.msdlive.org/records/65g71-a4731

EPA eGRID  
https://www.epa.gov/egrid/detailed-data

WRI Aqueduct  
https://www.wri.org/applications/aqueduct/water-risk-atlas/

---

# Data Processing

`code/preprocessing.py` reads raw datasets and generates derived analysis datasets.

Steps performed:

1. Load the **IM3 Data Center Atlas** (~1,479 facilities across 47 states)
2. Assign each facility to the **nearest EPA eGRID power plant**
3. Map facilities to **electricity grid subregions**
4. Merge **CO₂ emission rates** from EPA eGRID
5. Compute **baseline water stress metrics** from Aqueduct 4.0
6. Aggregate water stress indicators to **state and county levels**
7. Generate **future water stress projections (2030–2080)**

Derived datasets are written to:

```
data/derived-data/
```

---

# Downloading Raw Data

All raw datasets are included in the repository.  
To re-download them from source:

```bash
python code/download_data.py
```

Force re-download:

```bash
python code/download_data.py --force
```

---

# Usage

### 1. Download raw data

```bash
python code/download_data.py
```

### 2. Run preprocessing

```bash
python code/preprocessing.py
```

### 3. Generate static charts

```bash
python code/generate_charts.py
```

### 4. Launch the Streamlit dashboard

```bash
streamlit run streamlit-app/app.py
```

### 5. Render the project writeup

```bash
quarto render final_project.qmd
```

---

# Key Findings

- **1,474 unique data centers** across **47 U.S. states**
- Virginia (319), Texas (127), and California (112) host the largest concentrations
- The average electricity carbon intensity at data center locations is **~0.32 tCO₂e/MWh**
- **~27% of data centers** are located in **high or extremely high water-stress regions**
- Approximately **250 facilities face dual environmental risk**:
  - High electricity carbon intensity
  - High water stress

Future projections suggest that **water stress may intensify across North America through 2080**, increasing the importance of sustainable data center siting strategies.

---

# Policy Implications

The analysis suggests several policy considerations:

- Encourage **data center development in lower-carbon electricity regions**
- Incentivize **renewable energy procurement**
- Require **water impact assessments** for new data center permits
- Promote **water-efficient cooling technologies**
- Integrate **water stress indicators into infrastructure planning**

---

# License

MIT License

© 2026 Ankit Dixit and Manav Mutneja