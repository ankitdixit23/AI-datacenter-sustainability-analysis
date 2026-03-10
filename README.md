# AI Data Center Sustainability Analysis

**Spatial analysis of U.S. data center locations, grid carbon intensity, and regional water stress to evaluate sustainable siting policy.**

> UChicago Harris School — **DAP II (30538) Final Project**, Winter 2026  
> **Authors:** Manav Mutneja (`manavm-afk`) · Ankit Dixit (`ankitdixit23`)

---

## Research Question

**How do the locations of AI/cloud data centers in the United States relate to local carbon intensity of the electricity grid and regional water stress — and what are the policy implications for sustainable data center siting?**

### Sub-Questions

1. Which U.S. counties/states have the highest concentration of data centers, and how carbon-intensive is their local electricity grid?
2. Are data centers disproportionately located in water-stressed regions?
3. Under projected growth scenarios, how might future data center siting exacerbate or alleviate grid carbon and water stress?

---

## Live Dashboard

🔗 **[dc-sustainability.streamlit.app](https://dc-sustainability.streamlit.app)**

> The app may take **30–60 seconds to wake up** if it has been idle on Streamlit Community Cloud.

The interactive dashboard includes five pages:

- **Overview** — U.S. footprint explorer with labels on the national map, plus top states and counties by data center count
- **SQ1 · Carbon Intensity** — Top 10 eGRID subregions by data center count and renewable share vs. carbon intensity across eGRID subregions
- **SQ2 · Water Stress and Dual Burden** — Water stress distribution, high/extreme stress states, and a dual-burden explorer combining water stress and carbon intensity
- **SQ3 · Future Water Stress Projections** — WRI Aqueduct 4.0 future projections under Business-as-Usual, Optimistic, and Pessimistic scenarios across 2030, 2050, and 2080
- **Data Notes** — Dataset descriptions, methodology notes, definitions, and interpretation guidance

Each dashboard page also includes a **“How to read this dashboard”** section to help users interpret the visuals clearly.

---

## Setup

### Option A — Conda (recommended)

    conda env create -f environment.yml
    conda activate dc_sustainability

### Option B — pip

    pip install -r requirements.txt

---

## Project Structure

    ├── README.md
    ├── requirements.txt
    ├── environment.yml
    ├── .gitignore
    ├── Final_Project_Summary.qmd
    ├── Final_Project_Summary.html
    ├── Final_Project_Summary.pdf
    │
    ├── Streamlit_app/
    │   ├── app.py
    │   ├── requirements.txt
    │   ├── datacenters_master.csv
    │   ├── state_summary.csv
    │   ├── county_summary.csv
    │   ├── datacenters_with_water_stress.csv
    │   └── aqueduct_future_water_stress_na.csv
    │
    ├── code/
    │   ├── download_data.py
    │   ├── preprocessing.py
    │   └── generate_charts.py
    │
    ├── output_charts/
    │   ├── fig1_top_states.png
    │   ├── fig2a_us_map_states.png
    │   ├── fig2b_us_map_counties.png
    │   ├── fig3_egrid_subregions.png
    │   ├── fig4_water_stress.png
    │   └── fig5_dual_risk_scatter.png
    │
    └── data/                        ← excluded from git (see .gitignore)
        ├── raw-data/
        │   ├── im3_open_source_data_center_atlas_v2026.02.09.csv
        │   ├── egrid2023_data_rev2.xlsx
        │   ├── Aqueduct40_baseline_monthly_y2023m07d05.csv
        │   └── Aqueduct40_future_annual_y2023m07d05.csv
        │
        └── derived-data/
            ├── datacenters_master.csv
            ├── datacenters_with_emissions.csv
            ├── datacenters_with_water_stress.csv
            ├── county_summary.csv
            ├── state_summary.csv
            ├── aqueduct_annual_summary.csv
            ├── aqueduct_future_water_stress_na.csv
            └── water_stress_county_summary.csv

> **Note:** The `data/` directory is excluded from git due to file size limits. Raw data must be downloaded separately.

---

## Data Sources

| Dataset | Source | Format | Granularity |
|--------|--------|--------|-------------|
| **IM3 Open Source Data Center Atlas** | Pacific Northwest National Laboratory (PNNL / DOE) | CSV | Facility-level |
| **EPA eGRID 2023** | U.S. Environmental Protection Agency | XLSX | Plant / grid subregion |
| **WRI Aqueduct 4.0** | World Resources Institute | CSV | HydroSHEDS catchment |

**Download links:**

- IM3 Atlas: https://data.msdlive.org/records/65g71-a4731
- EPA eGRID: https://www.epa.gov/egrid/detailed-data
- WRI Aqueduct: https://www.wri.org/applications/aqueduct/water-risk-atlas/

---

## Usage

### 1. Download raw data

    python code/download_data.py

Force re-download:

    python code/download_data.py --force

### 2. Run preprocessing

    python code/preprocessing.py

### 3. Generate static charts

    python code/generate_charts.py

### 4. Launch the Streamlit dashboard

    streamlit run Streamlit_app/app.py

### 5. Render the project writeup

    quarto render Final_Project_Summary.qmd

---

## Data Processing

`code/preprocessing.py` reads raw datasets and generates derived analysis files.

Steps performed:

1. Load the **IM3 Data Center Atlas**
2. Assign facilities to relevant geographic units, including counties and states
3. Map facilities to **EPA eGRID subregions**
4. Merge **grid carbon intensity** measures from EPA eGRID
5. Merge **baseline water stress** metrics from WRI Aqueduct 4.0
6. Aggregate results to **state**, **county**, and **subregion** levels
7. Generate **future water stress projections (2030–2080)** for scenario analysis

---

## Dashboard Pages

### 1. Overview

The Overview page introduces the national footprint of U.S. data centers.

It includes:

- **U.S. footprint explorer**
- **Labels on the U.S. map**
- **Top states**
- **Top counties**

This page is designed to help users quickly identify where data centers are concentrated before moving into the carbon and water-risk analysis pages.

### 2. SQ1 · Carbon Intensity

This page answers the first sub-question by focusing on electricity-grid carbon intensity across data center locations.

It includes:

- **Top 10 eGRID subregions by data center count**
- **Renewable share vs. carbon intensity across eGRID subregions**

This section highlights whether the biggest data center hubs are concentrated in cleaner or more carbon-intensive power regions.

### 3. SQ2 · Water Stress and Dual Burden

This page answers the second sub-question by examining water stress and combined environmental risk.

It includes:

- Distribution of current facilities across water-stress categories
- States with the most facilities in **high / extremely high** water stress
- A **dual-burden explorer** combining water stress and carbon intensity
- Summary metrics for facilities in the dual-burden zone
- Top dual-burden states

**Dual burden definition:** facilities are flagged when they sit in **high or extremely high water stress** and also exceed the selected **carbon-intensity cutoff**.

### 4. SQ3 · Future Water Stress Projections

This page addresses the third sub-question by using **WRI Aqueduct 4.0** future scenario projections for North American catchments.

It includes:

- Scenario selection: **Business-as-Usual (BAU), Optimistic, Pessimistic**
- Summary indicators for the number of catchments under high/extreme stress
- **Water Stress Distribution Across Time Horizons**
- **Absolute Catchment Counts by Stress Level**
- **Raw Water Stress Score Distribution**
- A **Policy Implications** section interpreting the future siting risks

This page is intended to show how today’s siting choices may lock in long-term environmental exposure.

### 5. Data Notes

This page documents:

- Dataset descriptions
- Variable definitions
- Methodology notes
- Interpretation guidance
- Caveats and assumptions used in the dashboard

---

## Key Findings

- **1,474 unique data centers** across **47 U.S. states**
- Virginia, Texas, and California host the largest concentrations
- Average electricity carbon intensity at data center locations is approximately **0.32 tCO₂e/MWh**
- A meaningful share of facilities are located in **high or extremely high water-stress regions**
- A subset of facilities face **dual environmental burden**: both elevated water stress and elevated carbon intensity

Future projections suggest that water stress may intensify in some regions through 2080, increasing the importance of forward-looking siting strategies.

---

## Policy Implications

- Encourage **data center development in lower-carbon electricity regions**
- Incentivize **renewable energy procurement**
- Require **water impact assessments** for new data center permits
- Promote **water-efficient cooling technologies**
- Integrate **water stress indicators into infrastructure planning**
- Incorporate **long-horizon climate and water projections** into siting decisions for large-scale digital infrastructure

---

## License

MIT License

© 2026 Ankit Dixit and Manav Mutneja