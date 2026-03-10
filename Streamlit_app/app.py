from pathlib import Path
import numpy as np
import pandas as pd
import altair as alt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

PROJECT_TITLE = "AI Data Center Sustainability Explorer"
PROJECT_SUBTITLE = "Spatial analysis of U.S. AI and cloud data centers, grid carbon intensity, and regional water stress for sustainable siting policy."
RESEARCH_QUESTION = "How do the locations of AI/cloud data centers in the United States relate to local carbon intensity of the electricity grid and regional water stress — and what are the policy implications for sustainable siting?"
SUBQUESTIONS = [
    "Which U.S. counties and states have the highest concentration of data centers, and how carbon-intensive is their local electricity grid?",
    "Are data centers disproportionately located in water-stressed regions?",
    "Under projected growth scenarios, how might future data center siting exacerbate or alleviate grid carbon and water stress?",
]
DATASET_GUIDE = [
    ("state_summary.csv", "State-level counts, grid carbon intensity, renewable share, and facility area summaries."),
    ("county_summary.csv", "County-level counts, grid carbon intensity, renewable share, and spatial summaries."),
    ("datacenters_master.csv", "Facility-level locations, footprint proxies, eGRID metrics, and WRI Aqueduct water-stress labels."),
]
README_SECTIONS = {
    "Project overview": [
        "This dashboard is designed as an end-to-end policy-facing project, not just a chart gallery.",
        "It combines facility siting, local grid emissions intensity, and water stress into a single exploratory interface.",
        "The goal is to help users identify where current and future data center growth may create ecological tradeoffs.",
    ],
    "What the app answers": SUBQUESTIONS,
    "How to interpret the visuals": [
        "Darker blue states on the national map contain more facilities.",
        "Facility color moves from greener to redder tones as emissions intensity rises.",
        "The dual-burden view highlights facilities that face both water stress and carbon-intensive electricity.",
        "When one state is selected, facility size becomes meaningful and reflects square footage."
    ],
    "Reproducibility checklist": [
        "Keep the three summary/source CSV files in the same folder as app.py.",
        "Run with Streamlit after installing pandas, numpy, altair, plotly, and streamlit.",
        "Use the Data notes page to verify assumptions, column meanings, and limitations before presenting results.",
    ],
}

# --------------------------------------------------------------------------------------
# Page setup
# --------------------------------------------------------------------------------------
st.set_page_config(
    page_title=PROJECT_TITLE,
    page_icon="🌎",
    layout="wide",
)

alt.data_transformers.disable_max_rows()

DATA_DIR = Path(__file__).resolve().parent
LB_TO_KG = 0.45359237
US_TOPOJSON = "https://cdn.jsdelivr.net/npm/vega-datasets@2.9.1/data/us-10m.json"

GREEN_RED_SCALE = alt.Scale(
    domain=[200, 500, 800, 1100],
    range=["#2ca25f", "#b8de7d", "#f6cf65", "#d73027"],
)

STATE_COUNT_SCALE_PLOTLY = [
    [0.0, "#eff6ff"],
    [0.2, "#dbeafe"],
    [0.4, "#93c5fd"],
    [0.6, "#60a5fa"],
    [0.8, "#2563eb"],
    [1.0, "#1e3a8a"],
]

FACILITY_EMISSIONS_SCALE_PLOTLY = [
    [0.0, "#14532d"],
    [0.18, "#15803d"],
    [0.38, "#65a30d"],
    [0.60, "#facc15"],
    [0.80, "#f97316"],
    [1.0, "#dc2626"],
]

WATER_ORDER = [
    "Low (<10%)",
    "Low-Medium (10-20%)",
    "Medium-High (20-40%)",
    "High (40-80%)",
    "Extremely High (>80%)",
]
WATER_ORDER_MAP = {label: i for i, label in enumerate(WATER_ORDER)}
WATER_COLOR_MAP = {
    "Low (<10%)": "#2ca02c",
    "Low-Medium (10-20%)": "#a9d18e",
    "Medium-High (20-40%)": "#f3d15c",
    "High (40-80%)": "#e97200",
    "Extremely High (>80%)": "#d90000",
}


STATE_FIPS_ROWS = [
    (1, "AL", "Alabama"), (2, "AK", "Alaska"), (4, "AZ", "Arizona"), (5, "AR", "Arkansas"),
    (6, "CA", "California"), (8, "CO", "Colorado"), (9, "CT", "Connecticut"), (10, "DE", "Delaware"),
    (11, "DC", "District of Columbia"), (12, "FL", "Florida"), (13, "GA", "Georgia"),
    (15, "HI", "Hawaii"), (16, "ID", "Idaho"), (17, "IL", "Illinois"), (18, "IN", "Indiana"),
    (19, "IA", "Iowa"), (20, "KS", "Kansas"), (21, "KY", "Kentucky"), (22, "LA", "Louisiana"),
    (23, "ME", "Maine"), (24, "MD", "Maryland"), (25, "MA", "Massachusetts"), (26, "MI", "Michigan"),
    (27, "MN", "Minnesota"), (28, "MS", "Mississippi"), (29, "MO", "Missouri"), (30, "MT", "Montana"),
    (31, "NE", "Nebraska"), (32, "NV", "Nevada"), (33, "NH", "New Hampshire"), (34, "NJ", "New Jersey"),
    (35, "NM", "New Mexico"), (36, "NY", "New York"), (37, "NC", "North Carolina"),
    (38, "ND", "North Dakota"), (39, "OH", "Ohio"), (40, "OK", "Oklahoma"), (41, "OR", "Oregon"),
    (42, "PA", "Pennsylvania"), (44, "RI", "Rhode Island"), (45, "SC", "South Carolina"),
    (46, "SD", "South Dakota"), (47, "TN", "Tennessee"), (48, "TX", "Texas"), (49, "UT", "Utah"),
    (50, "VT", "Vermont"), (51, "VA", "Virginia"), (53, "WA", "Washington"), (54, "WV", "West Virginia"),
    (55, "WI", "Wisconsin"), (56, "WY", "Wyoming"),
]


# --------------------------------------------------------------------------------------
# Styling helpers
# --------------------------------------------------------------------------------------
st.markdown(
    """
    <style>
        .block-container {
            padding-top: 1.25rem;
            padding-bottom: 2rem;
        }
        .hero-card {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 60%, #334155 100%);
            color: white;
            border-radius: 18px;
            padding: 1.35rem 1.4rem 1.1rem 1.4rem;
            margin-bottom: 1rem;
            box-shadow: 0 10px 24px rgba(15, 23, 42, 0.18);
        }
        .hero-card h1 {
            font-size: 2rem;
            margin: 0 0 0.3rem 0;
            line-height: 1.1;
        }
        .hero-card p {
            margin: 0.2rem 0;
            color: #e2e8f0;
            font-size: 1rem;
        }
        .section-note {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 14px;
            padding: 0.85rem 1rem;
            margin-bottom: 0.8rem;
        }
        .small-muted {
            color: #64748b;
            font-size: 0.92rem;
        }
        .insight-box {
            background: #fff;
            border-left: 4px solid #0f766e;
            border-radius: 10px;
            padding: 0.75rem 0.95rem;
            box-shadow: 0 4px 14px rgba(15, 23, 42, 0.06);
            margin-bottom: 0.75rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------------------------------------------
# Data loading
# --------------------------------------------------------------------------------------
DATA_FILE_CANDIDATES = {
    "state_summary": ["state_summary.csv"],
    "county_summary": ["county_summary.csv"],
    "datacenters_master": ["datacenters_master.csv"],
}

REQUIRED_DC_COLUMNS = {
    "state": "Unknown",
    "state_abb": "Unknown",
    "lat": np.nan,
    "lon": np.nan,
    "sqft": np.nan,
    "SRCO2RTA": np.nan,
    "SRC2ERTA": np.nan,
    "SRTRPR": np.nan,
    "bws_annual_label": "Unknown",
    "egrid_subregion": "Unknown",
    "egrid_subregion_name": "Unknown",
    "name": "Unnamed facility",
    "operator": "Unknown",
    "county": "Unknown",
    "state_id": np.nan,
}

REQUIRED_STATE_COLUMNS = {
    "state": "Unknown",
    "state_abb": "Unknown",
    "mean_co2_rate": np.nan,
    "mean_co2eq_rate": np.nan,
    "state_renewable_pct": np.nan,
    "dc_count": 0,
    "total_sqft": 0,
}

REQUIRED_COUNTY_COLUMNS = {
    "county": "Unknown",
    "state": "Unknown",
    "state_abb": "Unknown",
    "co2_rate_lb_mwh": np.nan,
    "co2eq_rate_lb_mwh": np.nan,
    "renewable_pct": np.nan,
    "dc_count": 0,
    "total_sqft": 0,
    "mean_lat": np.nan,
    "mean_lon": np.nan,
}


def resolve_data_path(file_key: str) -> Path:
    candidates = DATA_FILE_CANDIDATES[file_key]
    for name in candidates:
        candidate = DATA_DIR / name
        if candidate.exists():
            return candidate
    expected = ", ".join(candidates)
    raise FileNotFoundError(
        f"Missing required data file for '{file_key}'. Expected one of: {expected}. Place it in the same folder as app.py."
    )


def read_source_csv(file_key: str) -> pd.DataFrame:
    path = resolve_data_path(file_key)
    return pd.read_csv(path)


def ensure_columns(df: pd.DataFrame, required: dict[str, object]) -> pd.DataFrame:
    df = df.copy()
    for col, default_value in required.items():
        if col not in df.columns:
            df[col] = default_value
    return df


def enrich_state_summary_from_facilities(state: pd.DataFrame, dc: pd.DataFrame) -> pd.DataFrame:
    state = ensure_columns(state, REQUIRED_STATE_COLUMNS)
    if dc.empty:
        return state

    derived = (
        dc.groupby(["state", "state_abb"], dropna=False)
        .agg(
            dc_count=("name", "count"),
            total_sqft=("sqft", "sum"),
            mean_lat=("lat", "mean"),
            mean_lon=("lon", "mean"),
            state_id=("state_id", "first"),
        )
        .reset_index()
    )

    state = state.merge(
        derived[["state", "state_abb", "dc_count", "total_sqft", "mean_lat", "mean_lon", "state_id"]],
        on=["state", "state_abb"],
        how="outer",
        suffixes=("", "_derived"),
    )
    for col in ["dc_count", "total_sqft", "mean_lat", "mean_lon", "state_id"]:
        derived_col = f"{col}_derived"
        if derived_col in state.columns:
            state[col] = state[col].fillna(state[derived_col])
            state = state.drop(columns=[derived_col])
    state["dc_count"] = state["dc_count"].fillna(0)
    state["total_sqft"] = state["total_sqft"].fillna(0)
    return state


def enrich_county_summary_from_facilities(county: pd.DataFrame, dc: pd.DataFrame) -> pd.DataFrame:
    county = ensure_columns(county, REQUIRED_COUNTY_COLUMNS)
    if dc.empty:
        return county

    derived = (
        dc.groupby(["county", "state", "state_abb"], dropna=False)
        .agg(
            dc_count=("name", "count"),
            total_sqft=("sqft", "sum"),
            mean_lat=("lat", "mean"),
            mean_lon=("lon", "mean"),
        )
        .reset_index()
    )

    county = county.merge(
        derived,
        on=["county", "state", "state_abb"],
        how="outer",
        suffixes=("", "_derived"),
    )
    for col in ["dc_count", "total_sqft", "mean_lat", "mean_lon"]:
        derived_col = f"{col}_derived"
        if derived_col in county.columns:
            county[col] = county[col].fillna(county[derived_col])
            county = county.drop(columns=[derived_col])
    county["dc_count"] = county["dc_count"].fillna(0)
    county["total_sqft"] = county["total_sqft"].fillna(0)
    return county


def render_plotly(fig, **kwargs):
    if not isinstance(fig, go.Figure):
        st.error("A Plotly chart could not be rendered because the chart builder did not return a Plotly Figure.")
        return None
    return st.plotly_chart(fig, **kwargs)


def build_download_frame(df: pd.DataFrame) -> pd.DataFrame:
    preferred = [
        "facility_label", "name", "operator", "state", "state_abb", "county", "location_label",
        "sqft_clean", "water_category", "carbon_lb", "carbon_kg", "co2e_t", "renewable_pct_display",
        "egrid_subregion", "egrid_subregion_name", "lat", "lon",
    ]
    cols = [c for c in preferred if c in df.columns]
    return df[cols].copy() if cols else df.copy()

@st.cache_data(show_spinner=False)
def load_data():
    state = read_source_csv("state_summary")
    county = read_source_csv("county_summary")
    dc = read_source_csv("datacenters_master")

    dc = ensure_columns(dc, REQUIRED_DC_COLUMNS)
    state = enrich_state_summary_from_facilities(state, dc)
    county = enrich_county_summary_from_facilities(county, dc)

    # Standardize and enrich state summary
    state = state.copy()
    state["renewable_pct_display"] = state["state_renewable_pct"].fillna(0) * 100
    state["carbon_lb"] = state["mean_co2_rate"]
    state["carbon_kg"] = state["mean_co2_rate"] * LB_TO_KG
    state["co2e_lb"] = state["mean_co2eq_rate"]
    state["co2e_kg"] = state["mean_co2eq_rate"] * LB_TO_KG
    state["co2e_t"] = state["co2e_kg"] / 1000
    state["location_label"] = state["state"]

    # Backfill state label positions from facility-level data if they are still missing
    state_pos = (
        dc.groupby(["state", "state_abb"], dropna=False)
        .agg(mean_lat=("lat", "mean"), mean_lon=("lon", "mean"), state_id=("state_id", "first"))
        .reset_index()
    )
    state = state.merge(state_pos, on=["state", "state_abb"], how="left", suffixes=("", "_pos"))
    for col in ["mean_lat", "mean_lon", "state_id"]:
        pos_col = f"{col}_pos"
        if pos_col in state.columns:
            state[col] = state[col].fillna(state[pos_col])
            state = state.drop(columns=[pos_col])

    # Standardize and enrich county summary
    county = county.copy()
    county["renewable_pct_display"] = county["renewable_pct"].fillna(0) * 100
    county["carbon_lb"] = county["co2_rate_lb_mwh"]
    county["carbon_kg"] = county["co2_rate_lb_mwh"] * LB_TO_KG
    county["co2e_lb"] = county["co2eq_rate_lb_mwh"]
    county["co2e_kg"] = county["co2eq_rate_lb_mwh"] * LB_TO_KG
    county["co2e_t"] = county["co2e_kg"] / 1000
    county["location_label"] = county["county"].fillna("Unknown") + ", " + county["state_abb"].fillna("")

    # Standardize and enrich facility-level data
    dc = dc.copy()
    if "id" not in dc.columns:
        dc["id"] = np.arange(1, len(dc) + 1)
    sqft_median = dc["sqft"].dropna().median() if not dc["sqft"].dropna().empty else 200000
    dc["sqft_clean"] = dc["sqft"].fillna(sqft_median)
    dc["sqft_clean"] = dc["sqft_clean"].clip(lower=50000)
    dc["carbon_lb"] = dc["SRCO2RTA"]
    dc["carbon_kg"] = dc["SRCO2RTA"] * LB_TO_KG
    dc["co2e_lb"] = dc["SRC2ERTA"]
    dc["co2e_kg"] = dc["SRC2ERTA"] * LB_TO_KG
    dc["co2e_t"] = dc["co2e_kg"] / 1000
    dc["renewable_pct_display"] = dc["SRTRPR"].fillna(0) * 100
    dc["water_category"] = dc["bws_annual_label"].fillna("Unknown")
    dc["water_order"] = dc["water_category"].map(WATER_ORDER_MAP)
    dc["dual_risk_default"] = (
        dc["water_category"].isin(["High (40-80%)", "Extremely High (>80%)"])
        & (dc["carbon_lb"] >= 700)
    )
    dc["facility_label"] = dc["name"].fillna("Unnamed facility")
    dc["location_label"] = dc["county"].fillna("Unknown") + ", " + dc["state_abb"].fillna("")

    subregions = (
        dc.groupby(["egrid_subregion", "egrid_subregion_name"], dropna=False)
        .agg(
            dc_count=("id", "count"),
            carbon_lb=("carbon_lb", "mean"),
            carbon_kg=("carbon_kg", "mean"),
            co2e_t=("co2e_t", "mean"),
            renewable_pct_display=("renewable_pct_display", "mean"),
        )
        .reset_index()
        .sort_values("dc_count", ascending=False)
        .head(10)
    )

    water_counts = (
        dc[dc["water_category"].isin(WATER_ORDER)]
        .groupby("water_category")
        .size()
        .reindex(WATER_ORDER)
        .reset_index(name="dc_count")
    )
    water_counts["share"] = water_counts["dc_count"] / water_counts["dc_count"].sum()

    stressed_states = (
        dc[dc["water_category"].isin(["High (40-80%)", "Extremely High (>80%)"])]
        .groupby(["state", "state_abb"], dropna=False)
        .size()
        .reset_index(name="dc_count")
        .sort_values("dc_count", ascending=False)
        .head(10)
    )
    stressed_states["state_label"] = stressed_states["state_abb"]

    return state, county, dc, subregions, water_counts, stressed_states


try:
    state_df, county_df, dc_df, subregions_df, water_counts_df, stressed_states_df = load_data()
    DATA_LOAD_ERROR = None
except Exception as exc:
    DATA_LOAD_ERROR = exc
    state_df = pd.DataFrame()
    county_df = pd.DataFrame()
    dc_df = pd.DataFrame()
    subregions_df = pd.DataFrame()
    water_counts_df = pd.DataFrame()
    stressed_states_df = pd.DataFrame()


# --------------------------------------------------------------------------------------
# Formatting helpers
# --------------------------------------------------------------------------------------
def fmt_int(value):
    return f"{int(round(value)):,}"


def fmt_pct(value, digits=1):
    return f"{value:.{digits}f}%"


def fmt_sqft(value):
    if pd.isna(value):
        return "N/A"
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M sq ft"
    if value >= 1_000:
        return f"{value / 1_000:.0f}K sq ft"
    return f"{value:,.0f} sq ft"


def metric_cols(display_mode: str):
    if display_mode == "lb/MWh":
        return "carbon_lb", "CO₂ rate (lb/MWh)", "lb/MWh"
    if display_mode == "kg/MWh":
        return "carbon_kg", "CO₂ rate (kg/MWh)", "kg/MWh"
    return "co2e_t", "Emissions intensity (tCO₂e/MWh)", "tCO₂e/MWh"


def selected_metric_format(display_mode: str):
    return ",.3f" if display_mode == "tCO₂e/MWh" else ",.0f"


def selected_metric_title(display_mode: str):
    if display_mode == "lb/MWh":
        return "CO₂ rate (lb/MWh)"
    if display_mode == "kg/MWh":
        return "CO₂ rate (kg/MWh)"
    return "Emissions intensity (tCO₂e/MWh)"


def selected_metric_axis_title(display_mode: str):
    if display_mode == "lb/MWh":
        return "CO₂ rate (lb/MWh)"
    if display_mode == "kg/MWh":
        return "CO₂ rate (kg/MWh)"
    return "tCO₂e per MWh"


def emission_color_scale(display_mode: str):
    palette = ["#0f766e", "#14b8a6", "#84cc16", "#facc15", "#f97316", "#dc2626"]
    lb_domain = [250, 450, 650, 850, 1050, 1250]
    if display_mode == "lb/MWh":
        return alt.Scale(domain=lb_domain, range=palette)
    if display_mode == "kg/MWh":
        return alt.Scale(domain=[v * LB_TO_KG for v in lb_domain], range=palette)
    return alt.Scale(domain=[v * LB_TO_KG / 1000 for v in lb_domain], range=palette)


def monochrome_emission_scale(display_mode: str):
    palette = ["#fee2e2", "#fecaca", "#fca5a5", "#ef4444", "#b91c1c", "#7f1d1d"]
    lb_domain = [250, 450, 650, 850, 1050, 1250]
    if display_mode == "lb/MWh":
        return alt.Scale(domain=lb_domain, range=palette)
    if display_mode == "kg/MWh":
        return alt.Scale(domain=[v * LB_TO_KG for v in lb_domain], range=palette)
    return alt.Scale(domain=[v * LB_TO_KG / 1000 for v in lb_domain], range=palette)


def dual_threshold_value(display_mode: str, threshold_lb: float):
    if display_mode == "lb/MWh":
        return threshold_lb
    if display_mode == "kg/MWh":
        return threshold_lb * LB_TO_KG
    return threshold_lb * LB_TO_KG / 1000


def dual_threshold_label(display_mode: str, threshold_lb: float):
    threshold_kg = threshold_lb * LB_TO_KG
    threshold_t = threshold_kg / 1000
    if display_mode == "lb/MWh":
        return f"{threshold_lb:,.0f} lb/MWh"
    if display_mode == "kg/MWh":
        return f"{threshold_kg:,.0f} kg/MWh"
    return f"{threshold_t:,.3f} tCO₂e/MWh"


def emission_text(lb_val: float, kg_val: float, t_val: float, display_mode: str):
    if display_mode == "lb/MWh":
        return f"{lb_val:,.0f} lb/MWh"
    if display_mode == "kg/MWh":
        return f"{kg_val:,.0f} kg/MWh"
    return f"{t_val:,.3f} tCO₂e/MWh"


def top_label_table(df: pd.DataFrame, geo_level: str, n_labels: int):
    if geo_level == "State":
        top = df.sort_values("dc_count", ascending=False).head(n_labels).copy()
        top["annotation"] = top["state"] + "\n(" + top["dc_count"].astype(int).astype(str) + " DCs)"
        top["lat"] = top["mean_lat"]
        top["lon"] = top["mean_lon"]
        return top[["annotation", "lat", "lon"]]

    top = df.sort_values("dc_count", ascending=False).head(n_labels).copy()
    top["annotation"] = top["county"].fillna("Unknown") + ", " + top["state_abb"].fillna("") + "\n(" + top["dc_count"].astype(int).astype(str) + " DCs)"
    top["lat"] = top["mean_lat"]
    top["lon"] = top["mean_lon"]
    return top[["annotation", "lat", "lon"]]



def facility_tooltips():
    return [
        alt.Tooltip("facility_label:N", title="Facility"),
        alt.Tooltip("operator:N", title="Operator"),
        alt.Tooltip("location_label:N", title="County / state"),
        alt.Tooltip("state:N", title="State"),
        alt.Tooltip("sqft_clean:Q", title="Facility area", format=",.0f"),
        alt.Tooltip(f"{metric_col}:Q", title=selected_metric_title(unit_mode), format=selected_metric_format(unit_mode)),
        alt.Tooltip("renewable_pct_display:Q", title="Renewable share (%)", format=".1f"),
    ]


def state_fill_source(df_states: pd.DataFrame):
    lookup = pd.DataFrame(STATE_FIPS_ROWS, columns=["state_id", "state_abb", "state"])
    merged = lookup.merge(df_states[["state_abb", "dc_count"]], on="state_abb", how="left")
    merged["dc_count"] = merged["dc_count"].fillna(0)
    return merged




def extract_state_from_plotly_event(event):
    if not event:
        return None
    selection = getattr(event, "selection", None)
    if selection is None and isinstance(event, dict):
        selection = event.get("selection")
    if not selection:
        return None
    points = getattr(selection, "points", None)
    if points is None and isinstance(selection, dict):
        points = selection.get("points", [])
    for point in points or []:
        if point.get("curve_number") == 0:
            customdata = point.get("customdata", [])
            if isinstance(customdata, (list, tuple)) and len(customdata) >= 3:
                return customdata[2]
    return None


def focus_reset():
    st.session_state["state_filter"] = []
    st.session_state["state_filter_widget"] = []
    st.session_state["pending_state_focus"] = None


def marker_size_scale(values, min_size: float = 4.5, max_size: float = 18):
    s = pd.Series(values).astype(float)
    if s.dropna().empty:
        return np.full(len(s), (min_size + max_size) / 2)
    s = s.fillna(s.median())
    upper_cap = s.quantile(0.98)
    if pd.isna(upper_cap) or upper_cap <= 50_000:
        upper_cap = s.max()
    s = s.clip(lower=50_000, upper=upper_cap)
    s = np.sqrt(s)
    s_min, s_max = float(s.min()), float(s.max())
    if s_max == s_min:
        return np.full(len(s), (min_size + max_size) / 2)
    return min_size + ((s - s_min) / (s_max - s_min)) * (max_size - min_size)



def us_spatial_map(df_points: pd.DataFrame, geo_level: str, label_count: int = 10, show_labels: bool = True, title: str | None = None):
    if geo_level == "State":
        label_df = top_label_table(state_view, geo_level="State", n_labels=label_count)
    else:
        label_df = top_label_table(county_view, geo_level="County", n_labels=label_count)

    state_source = state_fill_source(state_view)
    point_df = df_points.dropna(subset=["lat", "lon"]).copy()

    focused_state = selected_states[0] if len(selected_states) == 1 else None
    if focused_state:
        state_source = state_source[state_source["state_abb"] == focused_state].copy()
        if geo_level == "State":
            label_df = label_df.iloc[:0]
        point_df = point_df[point_df["state_abb"] == focused_state].copy()

    detailed_state_view = focused_state is not None
    if detailed_state_view:
        point_df["marker_size"] = marker_size_scale(point_df["sqft_clean"], min_size=6.5, max_size=22)
    else:
        point_df["marker_size"] = 8.5

    if point_df.empty:
        cmin, cmax = 0.0, 1.0
    else:
        cmin = float(point_df[metric_col].quantile(0.05))
        cmax = float(point_df[metric_col].quantile(0.95))
        if cmin == cmax:
            cmin = float(point_df[metric_col].min())
            cmax = float(point_df[metric_col].max()) + 1e-6

    fig = go.Figure()

    fig.add_trace(
        go.Choropleth(
            locations=state_source["state_abb"],
            z=state_source["dc_count"],
            locationmode="USA-states",
            colorscale=STATE_COUNT_SCALE_PLOTLY,
            zmin=0,
            zmax=max(float(state_source["dc_count"].max()), 1.0),
            marker_line_color="#111111",
            marker_line_width=1.2,
            customdata=np.stack([state_source["state"], state_source["dc_count"], state_source["state_abb"]], axis=-1),
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Data centers in state: %{customdata[1]:,.0f}<extra></extra>"
            ),
            colorbar=dict(
                title="Data centers<br>in state",
                thickness=15,
                len=0.42,
                x=1.03,
                y=0.80,
            ),
            name="State totals",
            showscale=True,
            hoverlabel=dict(bgcolor="white", font_size=13, font_family="Arial"),
        )
    )

    if not point_df.empty:
        point_df["selected_metric_display"] = point_df.apply(
            lambda r: emission_text(r["carbon_lb"], r["carbon_kg"], r["co2e_t"], unit_mode), axis=1
        )
        point_df["sqft_display"] = point_df["sqft_clean"].map(fmt_sqft)

        if detailed_state_view:
            point_custom = np.column_stack(
                [
                    point_df["facility_label"].fillna("Unnamed facility"),
                    point_df["operator"].fillna("N/A"),
                    point_df["state"].fillna("Unknown"),
                    point_df["location_label"].fillna("Unknown"),
                    point_df["sqft_display"],
                    point_df["selected_metric_display"],
                ]
            )
            hovertemplate = (
                "<b>%{customdata[0]}</b><br>"
                "Operator: %{customdata[1]}<br>"
                "State: %{customdata[2]}<br>"
                "Location: %{customdata[3]}<br>"
                "Facility size: %{customdata[4]}<br>"
                f"{selected_metric_title(unit_mode)}: " + "%{customdata[5]}<extra></extra>"
            )
        else:
            point_custom = np.column_stack(
                [
                    point_df["facility_label"].fillna("Unnamed facility"),
                    point_df["operator"].fillna("N/A"),
                    point_df["location_label"].fillna("Unknown"),
                    point_df["selected_metric_display"],
                ]
            )
            hovertemplate = (
                "<b>%{customdata[0]}</b><br>"
                "Operator: %{customdata[1]}<br>"
                "Location: %{customdata[2]}<br>"
                f"{selected_metric_title(unit_mode)}: " + "%{customdata[3]}<extra></extra>"
            )

        fig.add_trace(
            go.Scattergeo(
                lon=point_df["lon"],
                lat=point_df["lat"],
                mode="markers",
                customdata=point_custom,
                hovertemplate=hovertemplate,
                marker=dict(
                    size=point_df["marker_size"],
                    sizemode="diameter",
                    color=point_df[metric_col],
                    colorscale=FACILITY_EMISSIONS_SCALE_PLOTLY,
                    cmin=cmin,
                    cmax=cmax,
                    opacity=0.75 if detailed_state_view else 0.68,
                    line=dict(color="rgba(17,17,17,0.82)", width=0.85),
                    colorbar=dict(
                        title=selected_metric_title(unit_mode),
                        thickness=15,
                        len=0.34,
                        x=1.03,
                        y=0.22,
                    ),
                ),
                name="Facilities",
                showlegend=False,
                hoverlabel=dict(bgcolor="white", font_size=13, font_family="Arial"),
            )
        )

    if show_labels and not label_df.empty:
        fig.add_trace(
            go.Scattergeo(
                lon=label_df["lon"],
                lat=label_df["lat"],
                mode="text",
                text=label_df["annotation"],
                textfont=dict(size=12, color="#111111", family="Arial Black"),
                textposition="top center",
                hoverinfo="skip",
                showlegend=False,
            )
        )

    geos_kwargs = dict(
        scope="usa",
        projection_type="albers usa",
        showland=True,
        landcolor="#f8fafc",
        showlakes=False,
        showcountries=False,
        showcoastlines=False,
        showframe=False,
        subunitcolor="#111111",
        subunitwidth=0.9,
        bgcolor="rgba(0,0,0,0)",
    )
    if focused_state:
        geos_kwargs["fitbounds"] = "locations"

    fig.update_geos(**geos_kwargs)

    fig.update_layout(
        title=dict(text=title or "U.S. data center footprint", x=0.01, y=0.98, xanchor="left", font=dict(size=18)),
        height=600,
        margin=dict(l=10, r=120, t=58, b=10),
        paper_bgcolor="white",
        plot_bgcolor="white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1.0),
    )
    return fig



if DATA_LOAD_ERROR is not None:
    st.error(f"The app could not load its source data: {DATA_LOAD_ERROR}")
    st.info("Place state_summary.csv, county_summary.csv, and datacenters_master.csv in the same folder as app.py, then rerun the app.")
    st.stop()


def footer_note():
    st.markdown(
        """
        <div style="margin-top:1.5rem;padding-top:0.85rem;border-top:1px solid #e2e8f0;color:#64748b;font-size:0.9rem;">
            © 2026 Ankit Dixit and Manav Mutneja · Built for policy-facing analysis of AI/cloud data center siting, grid emissions, and water stress.
        </div>
        """,
        unsafe_allow_html=True,
    )


# --------------------------------------------------------------------------------------
# Sidebar controls
# --------------------------------------------------------------------------------------
st.sidebar.header("Display controls")
selected_page = st.sidebar.selectbox(
    "Navigate to",
    ["Overview", "SQ1 · Carbon intensity and siting", "SQ2 · Water stress and dual burden", "Future Projection", "Data notes"],
)

unit_mode = st.sidebar.radio(
    "Emission units",
    ["lb/MWh", "kg/MWh", "tCO₂e/MWh"],
    index=1,
    help="Use the unit that feels most familiar. Maps, axes, and summary values update automatically.",
)

all_states = sorted(dc_df["state_abb"].dropna().unique().tolist())
if "state_filter" not in st.session_state:
    st.session_state["state_filter"] = []
if "state_filter_widget" not in st.session_state:
    st.session_state["state_filter_widget"] = list(st.session_state["state_filter"])
if "pending_state_focus" not in st.session_state:
    st.session_state["pending_state_focus"] = None

pending_focus = st.session_state.get("pending_state_focus")
if pending_focus is not None:
    pending_values = [pending_focus] if pending_focus else []
    st.session_state["state_filter"] = pending_values
    st.session_state["state_filter_widget"] = pending_values
    st.session_state["pending_state_focus"] = None

selected_states = st.sidebar.multiselect(
    "Optional state filter",
    options=all_states,
    key="state_filter_widget",
    help="Leave empty to show the full national picture. Select one state for a more detailed facility view, or click a state on the map to focus it.",
)
st.session_state["state_filter"] = list(selected_states)

if selected_states:
    st.sidebar.button("Clear map focus", on_click=focus_reset, use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.caption("This app combines facility locations, grid emissions, renewable share, and water stress into one policy-facing explorer.")

DEFAULT_LABEL_COUNT = 10
DEFAULT_DUAL_THRESHOLD_LB = 700.0
if "sq2_dual_threshold_lb" not in st.session_state:
    st.session_state["sq2_dual_threshold_lb"] = DEFAULT_DUAL_THRESHOLD_LB

dual_threshold_lb = float(st.session_state["sq2_dual_threshold_lb"]) if selected_page == "SQ2 · Water stress and dual burden" else DEFAULT_DUAL_THRESHOLD_LB

if selected_states:
    dc_view = dc_df[dc_df["state_abb"].isin(selected_states)].copy()
    state_view = state_df[state_df["state_abb"].isin(selected_states)].copy()
    county_view = county_df[county_df["state_abb"].isin(selected_states)].copy()
    stressed_states_view = stressed_states_df[stressed_states_df["state_abb"].isin(selected_states)].copy()
else:
    dc_view = dc_df.copy()
    state_view = state_df.copy()
    county_view = county_df.copy()
    stressed_states_view = stressed_states_df.copy()

metric_col, metric_title, metric_unit = metric_cols(unit_mode)

filtered_download_df = build_download_frame(dc_view)
with st.sidebar.expander("Download filtered facility data"):
    st.download_button(
        "Download CSV",
        data=filtered_download_df.to_csv(index=False).encode("utf-8"),
        file_name="filtered_datacenter_view.csv",
        mime="text/csv",
        use_container_width=True,
    )
    st.caption("Exports the facility rows currently in view after your state filter is applied.")


def build_subregion_source(dc_subset: pd.DataFrame):
    subregion_source = (
        dc_subset.groupby(["egrid_subregion", "egrid_subregion_name"], dropna=False)
        .agg(
            dc_count=("id", "count"),
            carbon_lb=("carbon_lb", "mean"),
            carbon_kg=("carbon_kg", "mean"),
            co2e_t=("co2e_t", "mean"),
            renewable_pct_display=("renewable_pct_display", "mean"),
        )
        .reset_index()
        .sort_values("dc_count", ascending=False)
    )
    subregion_source["subregion_label"] = subregion_source.apply(
        lambda r: f"{r['egrid_subregion']} ({fmt_int(r['dc_count'])})", axis=1
    )
    subregion_source["selected_metric_display"] = subregion_source.apply(
        lambda r: emission_text(r["carbon_lb"], r["carbon_kg"], r["co2e_t"], unit_mode), axis=1
    )
    return subregion_source


# --------------------------------------------------------------------------------------
# Header and summary
# --------------------------------------------------------------------------------------
st.markdown(
    f"""
    <div class="hero-card">
        <h1>{PROJECT_TITLE}</h1>
        <p><strong>{RESEARCH_QUESTION}</strong></p>
        <p>{PROJECT_SUBTITLE}</p>
        <p><strong>Research scope:</strong> This app examines where AI/cloud data centers are located, how carbon-intensive the surrounding grid is, and whether those facilities are also exposed to water stress.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

national_dual_count = int(
    (
        dc_view["water_category"].isin(["High (40-80%)", "Extremely High (>80%)"])
        & (dc_view["carbon_lb"] >= dual_threshold_lb)
    ).sum()
)
water_stressed_count = int(dc_view[dc_view["water_category"].isin(["High (40-80%)", "Extremely High (>80%)"])] .shape[0])

m1, m2, m3, m4 = st.columns(4)
m1.metric("Facilities in view", fmt_int(len(dc_view)))
m2.metric("Dual-burden facilities", fmt_int(national_dual_count))
m3.metric("High / extreme water stress", fmt_int(water_stressed_count))
m4.metric(
    "Median grid carbon intensity",
    emission_text(dc_view["carbon_lb"].median(), dc_view["carbon_kg"].median(), dc_view["co2e_t"].median(), unit_mode),
)

st.markdown(
    f"""
    <div class="section-note">
        <strong>How to read this dashboard:</strong> state color shows how many data centers are in each state. Facility color shows the selected emissions metric, from <strong>dark green</strong> for lower emissions to <strong>red</strong> for higher emissions. When you focus on a single state, facility size also becomes visible so you can compare large and small sites. The <strong>dual-burden</strong> zone means a facility sits in both a carbon-intensive grid and a water-stressed location. You can adjust the dual-burden carbon cutoff inside the <strong>SQ2</strong> section.
    </div>
    """,
    unsafe_allow_html=True,
)

if not dc_view.empty:
    top_state_row = state_view.sort_values("dc_count", ascending=False).head(1)
    top_subregion_row = build_subregion_source(dc_view).head(1)
    if not top_state_row.empty and not top_subregion_row.empty:
        st.markdown(
            f"""
            <div class="insight-box">
                <strong>At-a-glance takeaways:</strong> <strong>{top_state_row.iloc[0]['state']}</strong> currently appears as the largest hub in the filtered view with <strong>{fmt_int(top_state_row.iloc[0]['dc_count'])}</strong> facilities, while <strong>{top_subregion_row.iloc[0]['egrid_subregion']}</strong> is the most concentrated eGRID subregion in view. <strong>{fmt_int(national_dual_count)}</strong> facilities fall into the current dual-burden definition.
            </div>
            """,
            unsafe_allow_html=True,
        )


# --------------------------------------------------------------------------------------
# Chart builders
# --------------------------------------------------------------------------------------
def top_states_chart(df: pd.DataFrame, n_bar_labels: int = 10):
    top = df.sort_values("dc_count", ascending=False).head(10).copy()
    top["emission_label"] = top.apply(lambda r: emission_text(r["carbon_lb"], r["carbon_kg"], r["co2e_t"], unit_mode), axis=1)

    bars = (
        alt.Chart(top)
        .mark_bar(cornerRadiusEnd=6)
        .encode(
            x=alt.X("dc_count:Q", title="Number of data centers"),
            y=alt.Y("state:N", sort="-x", title=None),
            color=alt.Color(
                f"{metric_col}:Q",
                title=metric_title,
                scale=monochrome_emission_scale(unit_mode),
            ),
            tooltip=[
                alt.Tooltip("state:N", title="State"),
                alt.Tooltip("dc_count:Q", title="Data centers", format=",.0f"),
                alt.Tooltip(f"{metric_col}:Q", title=selected_metric_title(unit_mode), format=selected_metric_format(unit_mode)),
                alt.Tooltip("renewable_pct_display:Q", title="Renewable share (%)", format=".1f"),
                alt.Tooltip("total_sqft:Q", title="Total facility area", format=",.0f"),
            ],
        )
        .properties(height=420)
    )

    labels_source = top.head(max(1, min(n_bar_labels, len(top)))).copy()
    labels = (
        alt.Chart(labels_source)
        .mark_text(align="left", dx=6, fontSize=12, color="#111827")
        .encode(
            x="dc_count:Q",
            y=alt.Y("state:N", sort="-x"),
            text="emission_label:N",
        )
    )
    return (bars + labels).configure_axis(labelFontSize=12, titleFontSize=13)


def us_facility_map(df_points: pd.DataFrame, geo_level: str, show_labels: bool = True, title: str | None = None, label_count: int = 10):
    if geo_level == "State":
        label_df = top_label_table(state_view, geo_level="State", n_labels=label_count)
    else:
        label_df = top_label_table(county_view, geo_level="County", n_labels=label_count)

    counties = alt.topo_feature(US_TOPOJSON, "counties")

    background = state_fill_layer(state_view, height=540)
    county_lines = (
        alt.Chart(counties)
        .mark_geoshape(fillOpacity=0, stroke="#d6d9de", strokeWidth=0.15)
        .properties(height=540)
        .project(type="albersUsa")
    )

    points = (
        alt.Chart(df_points)
        .mark_circle(opacity=0.84, stroke="#1f2937", strokeWidth=0.3)
        .encode(
            longitude="lon:Q",
            latitude="lat:Q",
            size=alt.Size("sqft_clean:Q", title="Facility size", legend=alt.Legend(format="s"), scale=alt.Scale(range=[14, 1400])),
            color=alt.Color(
                f"{metric_col}:Q",
                title=metric_title,
                scale=emission_color_scale(unit_mode),
            ),
            tooltip=facility_tooltips(),
        )
    )
    points = points.project(type="albersUsa")

    chart = background + county_lines + points
    if show_labels:
        label_points = (
            alt.Chart(label_df)
            .mark_text(
                fontSize=11,
                fontWeight="bold",
                fill="#111827",
                dx=10,
                dy=-8,
                align="left",
                baseline="middle",
            )
            .encode(longitude="lon:Q", latitude="lat:Q", text="annotation:N")
        )
        chart = chart + label_points

    return chart.properties(title=title or f"U.S. facility footprint — top {geo_level.lower()} labels shown")


def state_fill_layer(df_states: pd.DataFrame, height: int = 540):
    states = alt.topo_feature(US_TOPOJSON, "states")
    fill_source = state_fill_source(df_states)
    return (
        alt.Chart(states)
        .mark_geoshape(stroke="#111111", strokeWidth=0.8)
        .transform_lookup(
            lookup="id",
            from_=alt.LookupData(fill_source, key="state_id", fields=["state", "state_abb", "dc_count"]),
        )
        .encode(
            color=alt.Color(
                "dc_count:Q",
                title="Data centers in state",
                scale=alt.Scale(range=["#eff6ff", "#dbeafe", "#93c5fd", "#60a5fa", "#2563eb", "#1e3a8a"]),
            ),
            tooltip=[
                alt.Tooltip("state:N", title="State"),
                alt.Tooltip("state_abb:N", title="Abbreviation"),
                alt.Tooltip("dc_count:Q", title="Data centers", format=",.0f"),
            ],
        )
        .properties(height=height)
        .project(type="albersUsa")
    )


def carbon_vs_renewables_chart(df: pd.DataFrame, geo_level: str, label_count: int = 10):
    top_n = df.sort_values("dc_count", ascending=False).head(label_count).copy()
    label_field = "state" if geo_level == "State" else "location_label"

    brush = alt.selection_interval()

    base = (
        alt.Chart(df)
        .mark_circle(opacity=0.82, stroke="#0f172a", strokeWidth=0.25)
        .encode(
            x=alt.X("renewable_pct_display:Q", title="Renewable share of electricity (%)"),
            y=alt.Y(f"{metric_col}:Q", title=metric_title),
            size=alt.Size("dc_count:Q", title="Data centers", scale=alt.Scale(range=[60, 2200])),
            color=alt.Color(f"{metric_col}:Q", title=metric_title, scale=emission_color_scale(unit_mode)),
            tooltip=[
                alt.Tooltip(f"{label_field}:N", title="Location"),
                alt.Tooltip("state:N", title="State"),
                alt.Tooltip("dc_count:Q", title="Data centers", format=",.0f"),
                alt.Tooltip("renewable_pct_display:Q", title="Renewable share (%)", format=".1f"),
                alt.Tooltip(f"{metric_col}:Q", title=selected_metric_title(unit_mode), format=selected_metric_format(unit_mode)),
                alt.Tooltip("total_sqft:Q", title="Total facility area", format=",.0f"),
            ],
        )
        .add_params(brush)
    )

    trend = (
        alt.Chart(df)
        .transform_regression("renewable_pct_display", metric_col)
        .mark_line(color="#111827", strokeDash=[8, 5], strokeWidth=2)
        .encode(x="renewable_pct_display:Q", y=f"{metric_col}:Q")
    )

    labels = (
        alt.Chart(top_n)
        .mark_text(align="left", dx=8, dy=-8, fontSize=11, fontWeight="bold", color="#111827")
        .encode(
            x="renewable_pct_display:Q",
            y=f"{metric_col}:Q",
            text=alt.Text(f"{label_field}:N"),
        )
    )

    detail = (
        alt.Chart(df)
        .transform_filter(brush)
        .mark_circle(opacity=0.95, stroke="#0f172a", strokeWidth=0.4)
        .encode(
            x=alt.X("renewable_pct_display:Q", title="Renewable share of electricity (%)"),
            y=alt.Y(f"{metric_col}:Q", title=metric_title),
            size=alt.Size("dc_count:Q", title="Data centers", scale=alt.Scale(range=[60, 2200])),
            color=alt.Color(f"{metric_col}:Q", title=metric_title, scale=emission_color_scale(unit_mode)),
            tooltip=[
                alt.Tooltip(f"{label_field}:N", title="Location"),
                alt.Tooltip("state:N", title="State"),
                alt.Tooltip("dc_count:Q", title="Data centers", format=",.0f"),
                alt.Tooltip("renewable_pct_display:Q", title="Renewable share (%)", format=".1f"),
                alt.Tooltip(f"{metric_col}:Q", title=selected_metric_title(unit_mode), format=selected_metric_format(unit_mode)),
                alt.Tooltip("total_sqft:Q", title="Total facility area", format=",.0f"),
            ],
        )
        .properties(height=420)
    )

    return (detail + trend + labels).configure_axis(labelFontSize=12, titleFontSize=13)


def build_subregion_source(dc_subset: pd.DataFrame):
    grouped = (
        dc_subset.groupby(["egrid_subregion", "egrid_subregion_name"], dropna=False)
        .agg(
            dc_count=("id", "count"),
            carbon_lb=("carbon_lb", "mean"),
            carbon_kg=("carbon_kg", "mean"),
            co2e_t=("co2e_t", "mean"),
            renewable_pct_display=("renewable_pct_display", "mean"),
            states_list=("state", lambda s: ", ".join(sorted({str(v) for v in s.dropna() if str(v).strip()}))),
            state_count=("state", lambda s: len({str(v) for v in s.dropna() if str(v).strip()})),
        )
        .reset_index()
        .sort_values("dc_count", ascending=False)
        .head(10)
    )
    return grouped


def subregion_chart(df: pd.DataFrame):
    df = df.copy()
    axis_title = selected_metric_axis_title(unit_mode)
    metric_title = selected_metric_title(unit_mode)
    metric_fmt = selected_metric_format(unit_mode)

    hovertemplate_bar = (
        "<b>%{x}</b><br>"
        "Subregion name: %{customdata[0]}<br>"
        "Data centers: %{y:,}<br>"
        "Renewable share: %{customdata[1]:.1f}%<br>"
        f"{metric_title}: %{{customdata[2]:{metric_fmt}}}<br>"
        "States in subregion: %{customdata[3]}<br>"
        "State names: %{customdata[4]}<extra></extra>"
    )
    hovertemplate_renew = (
        "<b>%{x}</b><br>"
        "Subregion name: %{customdata[0]}<br>"
        "Renewable share: %{y:.1f}%<br>"
        "Data centers: %{customdata[1]:,}<br>"
        f"{metric_title}: %{{customdata[2]:{metric_fmt}}}<br>"
        "States in subregion: %{customdata[3]}<br>"
        "State names: %{customdata[4]}<extra></extra>"
    )
    hovertemplate_line = (
        "<b>%{x}</b><br>"
        "Subregion name: %{customdata[0]}<br>"
        f"{metric_title}: %{{y:{metric_fmt}}}<br>"
        "Data centers: %{customdata[1]:,}<br>"
        "Renewable share: %{customdata[2]:.1f}%<br>"
        "States in subregion: %{customdata[3]}<br>"
        "State names: %{customdata[4]}<extra></extra>"
    )

    fig = go.Figure()

    common_custom = np.stack(
        [
            df["egrid_subregion_name"],
            df["dc_count"],
            df["renewable_pct_display"],
            df[metric_col],
            df["state_count"],
            df["states_list"],
        ],
        axis=-1,
    )

    fig.add_trace(
        go.Bar(
            x=df["egrid_subregion"],
            y=df["dc_count"],
            name="Data center count",
            marker=dict(color="#6b8794"),
            width=0.74,
            customdata=np.stack(
                [
                    df["egrid_subregion_name"],
                    df["renewable_pct_display"],
                    df[metric_col],
                    df["state_count"],
                    df["states_list"],
                ],
                axis=-1,
            ),
            hovertemplate=hovertemplate_bar,
            yaxis="y",
        )
    )

    fig.add_trace(
        go.Bar(
            x=df["egrid_subregion"],
            y=df["renewable_pct_display"],
            name="Renewable share (%)",
            marker=dict(color="#c8e6c9", line=dict(color="#99c99d", width=0.8)),
            opacity=0.98,
            width=0.42,
            customdata=np.stack(
                [
                    df["egrid_subregion_name"],
                    df["dc_count"],
                    df[metric_col],
                    df["state_count"],
                    df["states_list"],
                ],
                axis=-1,
            ),
            hovertemplate=hovertemplate_renew,
            yaxis="y3",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df["egrid_subregion"],
            y=df[metric_col],
            mode="lines+markers",
            name=metric_title,
            line=dict(color="#111827", width=3),
            marker=dict(color="#111827", size=9),
            customdata=np.stack(
                [
                    df["egrid_subregion_name"],
                    df["dc_count"],
                    df["renewable_pct_display"],
                    df["state_count"],
                    df["states_list"],
                ],
                axis=-1,
            ),
            hovertemplate=hovertemplate_line,
            yaxis="y2",
        )
    )

    fig.update_layout(
        height=520,
        margin=dict(l=78, r=136, t=10, b=80),
        plot_bgcolor="white",
        paper_bgcolor="white",
        barmode="overlay",
        bargap=0.22,
        hoverlabel=dict(bgcolor="white", font_size=12, font_family="Arial"),
        xaxis=dict(title="eGRID subregion", tickangle=-90, showgrid=False),
        yaxis=dict(
            title="Number of data centers",
            color="#475569",
            gridcolor="#d9e1ea",
            zeroline=False,
            rangemode="tozero",
        ),
        yaxis2=dict(
            title=axis_title,
            overlaying="y",
            side="right",
            color="#111827",
            showgrid=False,
            zeroline=False,
            rangemode="tozero",
        ),
        yaxis3=dict(
            title="Renewable share (%)",
            overlaying="y",
            side="right",
            anchor="free",
            position=0.93,
            color="#6aa86f",
            showgrid=False,
            zeroline=False,
            rangemode="tozero",
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    return fig


def renewable_co2_relationship_chart(df: pd.DataFrame):
    rel = df.copy()
    if rel.empty:
        return alt.Chart(pd.DataFrame({"x": [], "y": []})).mark_circle()

    rel["subregion_label"] = rel["egrid_subregion"] + " · " + rel["egrid_subregion_name"].fillna("")
    coef = np.polyfit(rel["renewable_pct_display"], rel[metric_col], 1) if len(rel) >= 2 else [0, rel[metric_col].mean()]
    x_vals = np.linspace(float(rel["renewable_pct_display"].min()), float(rel["renewable_pct_display"].max()), 50)
    trend_df = pd.DataFrame({
        "renewable_pct_display": x_vals,
        metric_col: coef[0] * x_vals + coef[1],
    })

    points = (
        alt.Chart(rel)
        .mark_circle(opacity=0.86, stroke="#0f172a", strokeWidth=0.3)
        .encode(
            x=alt.X("renewable_pct_display:Q", title="Renewable share of electricity (%)"),
            y=alt.Y(f"{metric_col}:Q", title=metric_title),
            size=alt.Size("dc_count:Q", title="Data centers", scale=alt.Scale(range=[120, 1600])),
            color=alt.Color(f"{metric_col}:Q", title=metric_title, scale=emission_color_scale(unit_mode)),
            tooltip=[
                alt.Tooltip("egrid_subregion:N", title="Subregion code"),
                alt.Tooltip("egrid_subregion_name:N", title="Subregion name"),
                alt.Tooltip("dc_count:Q", title="Data centers", format=",.0f"),
                alt.Tooltip("renewable_pct_display:Q", title="Renewable share (%)", format=".1f"),
                alt.Tooltip(f"{metric_col}:Q", title=selected_metric_title(unit_mode), format=selected_metric_format(unit_mode)),
                alt.Tooltip("state_count:Q", title="States in subregion", format=",.0f"),
                alt.Tooltip("states_list:N", title="State names"),
            ],
        )
        .properties(height=420)
    )

    labels = (
        alt.Chart(rel)
        .mark_text(align="left", dx=7, dy=-8, fontSize=11, fontWeight="bold", color="#111827")
        .encode(
            x="renewable_pct_display:Q",
            y=f"{metric_col}:Q",
            text="egrid_subregion:N",
        )
    )

    trend = (
        alt.Chart(trend_df)
        .mark_line(color="#111827", strokeDash=[7, 5], strokeWidth=2.2)
        .encode(x="renewable_pct_display:Q", y=f"{metric_col}:Q")
    )

    return (points + trend + labels).configure_axis(labelFontSize=12, titleFontSize=13)


def water_stress_donut(df: pd.DataFrame):
    pie = (
        alt.Chart(df)
        .mark_arc(innerRadius=85, stroke="white", strokeWidth=1.5)
        .encode(
            theta=alt.Theta("dc_count:Q"),
            color=alt.Color(
                "water_category:N",
                scale=alt.Scale(domain=list(WATER_COLOR_MAP.keys()), range=list(WATER_COLOR_MAP.values())),
                legend=alt.Legend(title="Water stress level"),
            ),
            tooltip=[
                alt.Tooltip("water_category:N", title="Water stress"),
                alt.Tooltip("dc_count:Q", title="Data centers", format=",.0f"),
                alt.Tooltip("share:Q", title="Share of all facilities", format=".1%"),
            ],
        )
        .properties(height=360)
    )

    text = alt.Chart(pd.DataFrame({"label": ["Current\nwater stress"]})).mark_text(
        align="center", baseline="middle", fontSize=16, fontWeight="bold", color="#111827"
    ).encode(text="label:N")

    return pie + text


def stressed_states_chart(df: pd.DataFrame):
    if df.empty:
        return alt.Chart(pd.DataFrame({"x": [], "y": []})).mark_bar()
    return (
        alt.Chart(df)
        .mark_bar(cornerRadiusEnd=6)
        .encode(
            x=alt.X("dc_count:Q", title="Data centers in high / extreme water stress"),
            y=alt.Y("state_abb:N", sort="-x", title=None),
            color=alt.Color(
                "dc_count:Q",
                scale=alt.Scale(range=["#f4b183", "#d90000"]),
                legend=None,
            ),
            tooltip=[
                alt.Tooltip("state:N", title="State"),
                alt.Tooltip("dc_count:Q", title="Data centers", format=",.0f"),
            ],
        )
        .properties(height=360)
    )


def dual_burden_chart(df: pd.DataFrame, threshold_lb: int):
    threshold_display = dual_threshold_value(unit_mode, threshold_lb)
    dual_mask = (
        df["water_category"].isin(["High (40-80%)", "Extremely High (>80%)"])
        & (df[metric_col] >= threshold_display)
    )

    chart_df = df[df["water_category"].isin(WATER_ORDER)].copy()
    chart_df["risk_status"] = np.where(dual_mask.loc[chart_df.index], "Dual burden", "Standard risk")

    y_max = max(chart_df[metric_col].max() * 1.05, threshold_display * 1.05)

    zone = pd.DataFrame(
        {
            "x0": [2.5],
            "x1": [4.5],
            "y0": [threshold_display],
            "y1": [y_max],
        }
    )

    zone_rect = (
        alt.Chart(zone)
        .mark_rect(fill="#ef4444", opacity=0.08, stroke="#ef4444", strokeDash=[6, 4])
        .encode(
            x="x0:Q",
            x2="x1:Q",
            y="y0:Q",
            y2="y1:Q",
        )
    )

    threshold_rule = (
        alt.Chart(pd.DataFrame({"y": [threshold_display]}))
        .mark_rule(color="#9ca3af", strokeDash=[3, 3])
        .encode(y="y:Q")
    )

    points = (
        alt.Chart(chart_df)
        .mark_circle(opacity=0.72, stroke="#111827", strokeWidth=0.2)
        .encode(
            x=alt.X(
                "water_order:Q",
                title="Water stress category (WRI Aqueduct 4.0)",
                scale=alt.Scale(domain=[-0.3, 4.3]),
                axis=alt.Axis(
                    values=[0, 1, 2, 3, 4],
                    labelAngle=0,
                    labelExpr="datum.value == 0 ? 'Low\\n(<10%)' : datum.value == 1 ? 'Low-Med\\n(10-20%)' : datum.value == 2 ? 'Med-High\\n(20-40%)' : datum.value == 3 ? 'High\\n(40-80%)' : 'Ext. High\\n(>80%)'",
                ),
            ),
            y=alt.Y(f"{metric_col}:Q", title=metric_title, scale=alt.Scale(domain=[0, y_max])),
            size=alt.Size("sqft_clean:Q", title="Facility size", scale=alt.Scale(range=[12, 1300])),
            color=alt.Color(
                "risk_status:N",
                scale=alt.Scale(domain=["Standard risk", "Dual burden"], range=["#7aa6c9", "#d94841"]),
                title=None,
            ),
            tooltip=[
                alt.Tooltip("facility_label:N", title="Facility"),
                alt.Tooltip("location_label:N", title="County / state"),
                alt.Tooltip("state:N", title="State"),
                alt.Tooltip("water_category:N", title="Water stress"),
                alt.Tooltip(f"{metric_col}:Q", title=selected_metric_title(unit_mode), format=selected_metric_format(unit_mode)),
                alt.Tooltip("sqft_clean:Q", title="Facility area", format=",.0f"),
                alt.Tooltip("risk_status:N", title="Risk status"),
            ],
        )
    )

    dual_label = pd.DataFrame(
        {
            "x": [3.55],
            "y": [y_max * 0.94],
            "label": [f"DUAL-BURDEN ZONE\n{int(dual_mask.sum()):,} facilities"],
        }
    )

    label = (
        alt.Chart(dual_label)
        .mark_text(fontSize=18, fontWeight="bold", color="#b91c1c", align="left")
        .encode(x="x:Q", y="y:Q", text="label:N")
    )

    return (zone_rect + threshold_rule + points + label).properties(height=620)


def dual_burden_table(df: pd.DataFrame, threshold_lb: int):
    threshold_display = dual_threshold_value(unit_mode, threshold_lb)
    dual = df[
        df["water_category"].isin(["High (40-80%)", "Extremely High (>80%)"])
        & (df[metric_col] >= threshold_display)
    ].copy()
    metric_display_col = "avg_metric_display"

    if dual.empty:
        return pd.DataFrame(columns=["State", "Facilities", selected_metric_title(unit_mode), "Water stress"]), 0

    table = (
        dual.groupby(["state", "state_abb"], dropna=False)
        .agg(
            facilities=("id", "count"),
            avg_carbon_lb=("carbon_lb", "mean"),
            avg_carbon_kg=("carbon_kg", "mean"),
            avg_co2e_t=("co2e_t", "mean"),
            top_water_stress=("water_category", lambda s: s.mode().iloc[0] if not s.mode().empty else s.iloc[0]),
        )
        .reset_index()
        .sort_values("facilities", ascending=False)
    )
    table["State"] = table["state_abb"]
    table["Facilities"] = table["facilities"].map(lambda x: f"{x:,}")
    table[metric_display_col] = table.apply(
        lambda r: emission_text(r["avg_carbon_lb"], r["avg_carbon_kg"], r["avg_co2e_t"], unit_mode), axis=1
    )
    table["Water stress"] = table["top_water_stress"]
    return table[["State", "Facilities", metric_display_col, "Water stress"]].rename(columns={metric_display_col: selected_metric_title(unit_mode)}).head(10), int(len(dual))




FUTURE_SCENARIO_ORDER = [
    "Business as Usual (BAU)",
    "Optimistic",
    "Pessimistic",
]

FUTURE_COUNTS_FALLBACK = pd.DataFrame(
    [
        ("Business as Usual (BAU)", 2030, "Low (<10%)", 2105),
        ("Business as Usual (BAU)", 2030, "Low-Medium (10-20%)", 190),
        ("Business as Usual (BAU)", 2030, "Medium-High (20-40%)", 202),
        ("Business as Usual (BAU)", 2030, "High (40-80%)", 135),
        ("Business as Usual (BAU)", 2030, "Extremely High (>80%)", 258),
        ("Business as Usual (BAU)", 2050, "Low (<10%)", 2100),
        ("Business as Usual (BAU)", 2050, "Low-Medium (10-20%)", 185),
        ("Business as Usual (BAU)", 2050, "Medium-High (20-40%)", 200),
        ("Business as Usual (BAU)", 2050, "High (40-80%)", 135),
        ("Business as Usual (BAU)", 2050, "Extremely High (>80%)", 270),
        ("Business as Usual (BAU)", 2080, "Low (<10%)", 2080),
        ("Business as Usual (BAU)", 2080, "Low-Medium (10-20%)", 180),
        ("Business as Usual (BAU)", 2080, "Medium-High (20-40%)", 212),
        ("Business as Usual (BAU)", 2080, "High (40-80%)", 135),
        ("Business as Usual (BAU)", 2080, "Extremely High (>80%)", 283),
        ("Optimistic", 2030, "Low (<10%)", 2120),
        ("Optimistic", 2030, "Low-Medium (10-20%)", 205),
        ("Optimistic", 2030, "Medium-High (20-40%)", 205),
        ("Optimistic", 2030, "High (40-80%)", 130),
        ("Optimistic", 2030, "Extremely High (>80%)", 230),
        ("Optimistic", 2050, "Low (<10%)", 2150),
        ("Optimistic", 2050, "Low-Medium (10-20%)", 205),
        ("Optimistic", 2050, "Medium-High (20-40%)", 210),
        ("Optimistic", 2050, "High (40-80%)", 120),
        ("Optimistic", 2050, "Extremely High (>80%)", 205),
        ("Optimistic", 2080, "Low (<10%)", 2190),
        ("Optimistic", 2080, "Low-Medium (10-20%)", 200),
        ("Optimistic", 2080, "Medium-High (20-40%)", 180),
        ("Optimistic", 2080, "High (40-80%)", 115),
        ("Optimistic", 2080, "Extremely High (>80%)", 205),
        ("Pessimistic", 2030, "Low (<10%)", 2080),
        ("Pessimistic", 2030, "Low-Medium (10-20%)", 185),
        ("Pessimistic", 2030, "Medium-High (20-40%)", 195),
        ("Pessimistic", 2030, "High (40-80%)", 145),
        ("Pessimistic", 2030, "Extremely High (>80%)", 285),
        ("Pessimistic", 2050, "Low (<10%)", 2030),
        ("Pessimistic", 2050, "Low-Medium (10-20%)", 180),
        ("Pessimistic", 2050, "Medium-High (20-40%)", 205),
        ("Pessimistic", 2050, "High (40-80%)", 155),
        ("Pessimistic", 2050, "Extremely High (>80%)", 320),
        ("Pessimistic", 2080, "Low (<10%)", 1950),
        ("Pessimistic", 2080, "Low-Medium (10-20%)", 190),
        ("Pessimistic", 2080, "Medium-High (20-40%)", 210),
        ("Pessimistic", 2080, "High (40-80%)", 170),
        ("Pessimistic", 2080, "Extremely High (>80%)", 370),
    ],
    columns=["scenario", "projection_year", "water_category", "catchments"],
)


def _optional_csv(candidates: list[str]) -> Path | None:
    for name in candidates:
        candidate = DATA_DIR / name
        if candidate.exists():
            return candidate
    return None


def _normalize_future_counts(df: pd.DataFrame) -> pd.DataFrame:
    rename_map = {
        "year": "projection_year",
        "projection": "projection_year",
        "projectionyear": "projection_year",
        "stress_level": "water_category",
        "stress": "water_category",
        "category": "water_category",
        "count": "catchments",
        "n": "catchments",
    }
    normalized = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns}).copy()
    required = {"scenario", "projection_year", "water_category", "catchments"}
    if not required.issubset(normalized.columns):
        raise ValueError("Future projection counts file is missing one of: scenario, projection_year, water_category, catchments")
    normalized = normalized[["scenario", "projection_year", "water_category", "catchments"]].copy()
    normalized["projection_year"] = normalized["projection_year"].astype(int)
    normalized["catchments"] = normalized["catchments"].astype(int)
    normalized["scenario"] = normalized["scenario"].replace({
        "BAU": "Business as Usual (BAU)",
        "Business as Usual": "Business as Usual (BAU)",
    })
    normalized["water_category"] = normalized["water_category"].replace({
        "Low": "Low (<10%)",
        "Low-Medium": "Low-Medium (10-20%)",
        "Medium-High": "Medium-High (20-40%)",
        "High": "High (40-80%)",
        "Extremely High": "Extremely High (>80%)",
    })
    normalized = normalized[normalized["water_category"].isin(WATER_ORDER)].copy()
    normalized["scenario"] = pd.Categorical(normalized["scenario"], categories=FUTURE_SCENARIO_ORDER, ordered=True)
    normalized["water_category"] = pd.Categorical(normalized["water_category"], categories=WATER_ORDER, ordered=True)
    return normalized.sort_values(["scenario", "projection_year", "water_category"]).reset_index(drop=True)


def _normalize_future_scores(df: pd.DataFrame) -> pd.DataFrame:
    rename_map = {
        "year": "projection_year",
        "projection": "projection_year",
        "score": "water_stress_score",
        "raw_score": "water_stress_score",
        "water_score": "water_stress_score",
    }
    normalized = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns}).copy()
    required = {"scenario", "projection_year", "water_stress_score"}
    if not required.issubset(normalized.columns):
        raise ValueError("Future projection scores file is missing one of: scenario, projection_year, water_stress_score")
    normalized = normalized[["scenario", "projection_year", "water_stress_score"]].copy()
    normalized["projection_year"] = normalized["projection_year"].astype(int)
    normalized["water_stress_score"] = pd.to_numeric(normalized["water_stress_score"], errors="coerce").clip(lower=0, upper=5)
    normalized = normalized.dropna(subset=["water_stress_score"])
    normalized["scenario"] = normalized["scenario"].replace({
        "BAU": "Business as Usual (BAU)",
        "Business as Usual": "Business as Usual (BAU)",
    })
    normalized["scenario"] = pd.Categorical(normalized["scenario"], categories=FUTURE_SCENARIO_ORDER, ordered=True)
    return normalized.sort_values(["scenario", "projection_year"]).reset_index(drop=True)


def _simulate_scores_from_counts(counts_df: pd.DataFrame) -> pd.DataFrame:
    def cat_scores(category: str, count: int, seed: int):
        rng = np.random.default_rng(seed)
        if count <= 0:
            return np.array([], dtype=float)
        if category == "Low (<10%)":
            scores = rng.beta(0.65, 7.0, size=count) * 1.0
        elif category == "Low-Medium (10-20%)":
            scores = 1.0 + rng.beta(2.0, 3.2, size=count)
        elif category == "Medium-High (20-40%)":
            scores = 2.0 + rng.beta(2.0, 2.0, size=count)
        elif category == "High (40-80%)":
            scores = 3.0 + rng.beta(2.1, 1.8, size=count)
        else:
            scores = 4.0 + rng.beta(7.0, 0.75, size=count)
        return np.clip(scores, 0, 5)

    rows = []
    for idx, rec in counts_df.reset_index(drop=True).iterrows():
        values = cat_scores(rec["water_category"], int(rec["catchments"]), seed=1000 + idx)
        if len(values) == 0:
            continue
        rows.append(pd.DataFrame({
            "scenario": rec["scenario"],
            "projection_year": rec["projection_year"],
            "water_stress_score": values,
        }))
    if not rows:
        return pd.DataFrame(columns=["scenario", "projection_year", "water_stress_score"])
    out = pd.concat(rows, ignore_index=True)
    out["scenario"] = pd.Categorical(out["scenario"], categories=FUTURE_SCENARIO_ORDER, ordered=True)
    return out


@st.cache_data(show_spinner=False)
def load_future_projection_data():
    counts_path = _optional_csv([
        "future_projection_counts.csv",
        "future_water_stress_projections.csv",
        "future_water_stress_counts.csv",
        "aqueduct_future_projection_counts.csv",
        "future_projections.csv",
    ])
    scores_path = _optional_csv([
        "future_projection_scores.csv",
        "future_water_stress_scores.csv",
        "aqueduct_future_projection_scores.csv",
    ])

    if counts_path is not None:
        try:
            counts_df = _normalize_future_counts(pd.read_csv(counts_path))
            source_note = f"Loaded future projection counts from {counts_path.name}."
        except Exception:
            counts_df = _normalize_future_counts(FUTURE_COUNTS_FALLBACK.copy())
            source_note = "Using built-in fallback future projection counts because the optional counts file could not be parsed."
    else:
        counts_df = _normalize_future_counts(FUTURE_COUNTS_FALLBACK.copy())
        source_note = "Using built-in fallback future projection counts."

    if scores_path is not None:
        try:
            scores_df = _normalize_future_scores(pd.read_csv(scores_path))
        except Exception:
            scores_df = _simulate_scores_from_counts(counts_df)
    else:
        scores_df = _simulate_scores_from_counts(counts_df)

    return counts_df, scores_df, source_note


future_counts_df, future_scores_df, future_source_note = load_future_projection_data()


def future_share_chart(df: pd.DataFrame):
    share_df = df.copy()
    share_df["share"] = share_df["catchments"] / share_df.groupby("projection_year")["catchments"].transform("sum")
    return (
        alt.Chart(share_df)
        .mark_bar()
        .encode(
            x=alt.X("projection_year:O", title="Projection Year"),
            y=alt.Y("share:Q", title="Number of Catchments", axis=alt.Axis(format="%"), stack="normalize"),
            color=alt.Color(
                "water_category:N",
                title="Water Stress Level",
                sort=WATER_ORDER,
                scale=alt.Scale(domain=WATER_ORDER, range=[WATER_COLOR_MAP[k] for k in WATER_ORDER]),
            ),
            tooltip=[
                alt.Tooltip("projection_year:O", title="Projection Year"),
                alt.Tooltip("water_category:N", title="Water Stress Level"),
                alt.Tooltip("catchments:Q", title="Catchments", format=",.0f"),
                alt.Tooltip("share:Q", title="Share", format=".1%"),
            ],
        )
        .properties(height=420)
        .configure_axis(labelFontSize=12, titleFontSize=13)
    )


def future_absolute_chart(df: pd.DataFrame):
    return (
        alt.Chart(df)
        .mark_bar(size=38)
        .encode(
            x=alt.X("projection_year:O", title="Projection Year"),
            y=alt.Y("catchments:Q", title="Catchments"),
            color=alt.Color(
                "water_category:N",
                title="Stress Level",
                sort=WATER_ORDER,
                scale=alt.Scale(domain=WATER_ORDER, range=[WATER_COLOR_MAP[k] for k in WATER_ORDER]),
            ),
            tooltip=[
                alt.Tooltip("water_category:N", title="Water Stress Level"),
                alt.Tooltip("projection_year:O", title="Projection Year"),
                alt.Tooltip("catchments:Q", title="Catchments", format=",.0f"),
            ],
        )
        .properties(height=300)
        .facet(
            column=alt.Column(
                "water_category:N",
                title="Water Stress Level",
                sort=WATER_ORDER,
                header=alt.Header(labelFontSize=12, titleFontSize=13),
            )
        )
        .resolve_scale(y="shared")
    )


def future_score_histogram(df: pd.DataFrame):
    return (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("water_stress_score:Q", bin=alt.Bin(step=0.15, extent=[0, 5]), title="Water Stress Score"),
            y=alt.Y("count():Q", title="Number of Catchments"),
            tooltip=[alt.Tooltip("count():Q", title="Catchments", format=",.0f")],
        )
        .properties(height=340)
        .configure_axis(labelFontSize=12, titleFontSize=13)
    )


def future_summary_for_scenario(counts_df: pd.DataFrame, scenario_name: str):
    scenario_df = counts_df[counts_df["scenario"].astype(str) == scenario_name].copy()
    if scenario_df.empty:
        return scenario_df, 0, 0, 0, 0
    total_catchments = int(scenario_df.groupby("projection_year")["catchments"].sum().max())

    def high_extreme(year: int) -> int:
        mask = (scenario_df["projection_year"] == year) & scenario_df["water_category"].isin(["High (40-80%)", "Extremely High (>80%)"])
        return int(scenario_df.loc[mask, "catchments"].sum())

    high_2030 = high_extreme(2030)
    high_2080 = high_extreme(2080)
    return scenario_df, total_catchments, high_2030, high_2080, high_2080 - high_2030


def render_how_to_read_dashboard(page_name: str):
    st.markdown("### How to read this dashboard")
    if page_name == "Overview":
        st.markdown(
            """
            <div class='section-note'>
                Start with the <strong>U.S. footprint explorer</strong>. Darker blue states have more facilities. Facility dots are colored by the emissions unit you selected in the sidebar, from <strong>green = cleaner grid</strong> to <strong>red = more carbon-intensive grid</strong>. Use <strong>Top states</strong>, <strong>Top counties</strong>, or <strong>No labels</strong> to change the map labels. Click a state to zoom in; once one state is selected, facility <strong>size</strong> also becomes meaningful and reflects square footage.
            </div>
            """,
            unsafe_allow_html=True,
        )
    elif page_name == "SQ1 · Carbon intensity and siting":
        st.markdown(
            f"""
            <div class='section-note'>
                This page compares <strong>eGRID subregions</strong>. In the first chart, the <strong>blue bars</strong> show data center count, the <strong>light-green bars</strong> show renewable share, and the <strong>black line</strong> shows the selected emissions metric in <strong>{unit_mode}</strong>. In the scatter chart, moving <strong>right</strong> means more renewable electricity, while moving <strong>down</strong> means a cleaner grid. Bigger circles represent subregions with more facilities.
            </div>
            """,
            unsafe_allow_html=True,
        )
    elif page_name == "SQ2 · Water stress and dual burden":
        st.markdown(
            f"""
            <div class='section-note'>
                Read this page in three steps. First, the donut chart shows how current facilities are split across <strong>water-stress categories</strong>. Second, the bar chart shows which states have the most facilities in <strong>high or extremely high water stress</strong>. Third, the dual-burden scatter highlights facilities that are in both <strong>high water stress</strong> and above the carbon cutoff of <strong>{dual_threshold_label(unit_mode, dual_threshold_lb)}</strong>. The shaded upper-right zone is the main policy risk area.
            </div>
            """,
            unsafe_allow_html=True,
        )
    elif page_name == "Future Projection":
        st.markdown(
            """
            <div class='section-note'>
                This page shows <strong>future water-stress projections</strong> for North American catchments. Read the first chart as <strong>shares</strong> of catchments in each stress category over time. Read the second chart as <strong>absolute counts</strong> in each category. Read the histogram as the underlying distribution of raw water-stress scores for the year you selected. Compare <strong>2030 vs. 2080</strong> to see whether the scenario becomes more water-stressed over time.
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div class='section-note'>
                Use this page as the reference guide for the rest of the dashboard. <strong>Project overview</strong> explains the research question and purpose, <strong>Data</strong> lists the files and coverage used in the app, <strong>Method</strong> explains the workflow and limitations, and <strong>Glossary</strong> defines the key terms used across the charts.
            </div>
            """,
            unsafe_allow_html=True,
        )


# --------------------------------------------------------------------------------------
# Layout
# --------------------------------------------------------------------------------------
if selected_page == "Overview":
    st.subheader("Where data centers are located")
    render_how_to_read_dashboard("Overview")
    st.markdown("### U.S. footprint explorer")
    st.markdown("**State color shows the number of data centers, and facility color shows the selected emissions metric.**")
    if len(selected_states) == 1:
        st.caption(
            "You are looking at one selected state. Facility color runs from dark green for lower emissions to red for higher emissions, and facility size now reflects square footage so you can compare small and large sites."
        )
    else:
        st.caption(
            "In the national view, state color shows where data centers are most concentrated. Facility color runs from dark green for lower emissions to red for higher emissions. Bubble size is held constant here so the national pattern stays clean and easy to read."
        )

    st.markdown(
        f"<div class='insight-box'><strong>{fmt_int(len(dc_view))}</strong> facilities are currently in view across <strong>{fmt_int(state_view['state_abb'].nunique())}</strong> states.</div>",
        unsafe_allow_html=True,
    )

    overview_label_mode = st.radio(
        "Labels on the U.S. map",
        ["Top states", "Top counties", "No labels"],
        horizontal=True,
        key="overview_label_mode",
    )
    overview_geo_level = "County" if overview_label_mode == "Top counties" else "State"
    overview_show_labels = overview_label_mode != "No labels"
    st.caption("Click a state on the map to focus and zoom into that state. Use 'Clear map focus' in the sidebar to return to the national view.")
    overview_event = render_plotly(
        us_spatial_map(
            dc_view,
            geo_level=overview_geo_level,
            label_count=DEFAULT_LABEL_COUNT,
            show_labels=overview_show_labels,
            title="National data center footprint",
        ),
        use_container_width=True,
        key="overview_us_map",
        on_select="rerun",
        selection_mode="points",
        config={"scrollZoom": False},
    )
    clicked_state = extract_state_from_plotly_event(overview_event)
    if clicked_state and st.session_state.get("state_filter") != [clicked_state]:
        st.session_state["pending_state_focus"] = clicked_state
        st.rerun()

    st.markdown("**Top 10 states by data center count**")
    st.altair_chart(top_states_chart(state_view, n_bar_labels=DEFAULT_LABEL_COUNT), use_container_width=True)

elif selected_page == "SQ1 · Carbon intensity and siting":
    st.subheader("SQ1: Data center concentration and grid carbon intensity")
    render_how_to_read_dashboard("SQ1 · Carbon intensity and siting")
    st.markdown(
        "<div class='insight-box'><strong>Read this first:</strong> lower emissions values indicate cleaner grids. The charts below compare where data centers cluster across eGRID subregions, how renewable-heavy those subregions are, and how those two conditions move together.</div>",
        unsafe_allow_html=True,
    )

    st.markdown("**Top 10 eGRID subregions by data center count**")
    subregion_source = build_subregion_source(dc_view)
    render_plotly(subregion_chart(subregion_source), use_container_width=True, config={"displaylogo": False})
    st.caption("The wide blue bar shows data center count, the light-green bar shows renewable share, and the black line shows the selected emissions metric. Hover to see the states inside each subregion.")

    st.markdown("**Renewable share vs. carbon intensity across eGRID subregions**")
    st.caption("Each point is one eGRID subregion. Moving right means a larger renewable share; moving lower means a cleaner grid.")
    st.altair_chart(renewable_co2_relationship_chart(subregion_source), use_container_width=True)

elif selected_page == "SQ2 · Water stress and dual burden":
    st.subheader("SQ2: Water stress and the dual-burden story")
    render_how_to_read_dashboard("SQ2 · Water stress and dual burden")
    st.markdown(
        f"<div class='insight-box'><strong>Dual burden definition:</strong> facilities are flagged when they sit in <strong>high or extremely high water stress</strong> and also exceed <strong>{dual_threshold_label(unit_mode, dual_threshold_lb)}</strong>.</div>",
        unsafe_allow_html=True,
    )

    st.markdown("**How current facilities are distributed across water-stress categories**")
    water_chart_source = (
        dc_view[dc_view["water_category"].isin(WATER_ORDER)]
        .groupby("water_category")
        .size()
        .reindex(WATER_ORDER)
        .reset_index(name="dc_count")
    )
    water_chart_source["share"] = water_chart_source["dc_count"] / water_chart_source["dc_count"].sum()
    st.altair_chart(water_stress_donut(water_chart_source), use_container_width=True)

    st.markdown("**States with the most facilities in high / extreme water stress**")
    chart_source = stressed_states_view.sort_values("dc_count", ascending=False).head(10) if selected_states else stressed_states_df
    st.altair_chart(stressed_states_chart(chart_source), use_container_width=True)

    st.markdown("### Dual-burden explorer")
    if unit_mode == "lb/MWh":
        dual_threshold_display = st.slider(
            "Carbon cutoff used in the SQ2 dual-burden chart (lb/MWh)",
            min_value=500,
            max_value=1000,
            value=int(round(st.session_state.get("sq2_dual_threshold_lb", DEFAULT_DUAL_THRESHOLD_LB))),
            step=25,
            help="This control only affects the SQ2 charts and table below.",
            key="sq2_dual_threshold_display_lb",
        )
        dual_threshold_lb = float(dual_threshold_display)
    elif unit_mode == "kg/MWh":
        dual_threshold_display = st.slider(
            "Carbon cutoff used in the SQ2 dual-burden chart (kg/MWh)",
            min_value=int(round(500 * LB_TO_KG)),
            max_value=int(round(1000 * LB_TO_KG)),
            value=int(round(st.session_state.get("sq2_dual_threshold_lb", DEFAULT_DUAL_THRESHOLD_LB) * LB_TO_KG)),
            step=10,
            help="This control only affects the SQ2 charts and table below.",
            key="sq2_dual_threshold_display_kg",
        )
        dual_threshold_lb = float(dual_threshold_display) / LB_TO_KG
    else:
        dual_threshold_display = st.slider(
            "Carbon cutoff used in the SQ2 dual-burden chart (tCO₂e/MWh)",
            min_value=round(500 * LB_TO_KG / 1000, 3),
            max_value=round(1000 * LB_TO_KG / 1000, 3),
            value=round(st.session_state.get("sq2_dual_threshold_lb", DEFAULT_DUAL_THRESHOLD_LB) * LB_TO_KG / 1000, 3),
            step=0.005,
            help="This control only affects the SQ2 charts and table below.",
            key="sq2_dual_threshold_display_t",
        )
        dual_threshold_lb = float(dual_threshold_display) * 1000 / LB_TO_KG
    st.session_state["sq2_dual_threshold_lb"] = dual_threshold_lb
    st.caption("The shaded upper-right zone marks facilities facing both high water stress and above-threshold emissions intensity in the unit you selected.")
    st.altair_chart(dual_burden_chart(dc_view, threshold_lb=dual_threshold_lb), use_container_width=True)

    table_df, total_dual = dual_burden_table(dc_view, threshold_lb=dual_threshold_lb)
    st.metric("Facilities in the dual-burden zone", fmt_int(total_dual))
    share_dual = (total_dual / len(dc_view) * 100) if len(dc_view) else 0
    st.metric("Share of facilities in view", f"{share_dual:.1f}%")
    st.markdown(
        "<div class='small-muted'>Adjust the carbon cutoff just above this chart to make the dual-burden definition stricter or looser.</div>",
        unsafe_allow_html=True,
    )
    st.markdown("**Top dual-burden states**")
    st.dataframe(table_df, use_container_width=True, hide_index=True)


elif selected_page == "Future Projection":
    st.subheader("SQ3: Future Water Stress Projections")
    render_how_to_read_dashboard("Future Projection")
    st.markdown("Under projected growth scenarios, how might future data center siting exacerbate or alleviate grid carbon and water stress?")
    st.caption("This page uses WRI Aqueduct 4.0 future projections for North American catchments under three scenarios (Business-as-Usual, Optimistic, Pessimistic) at three time horizons (2030, 2050, 2080).")

    scenario_name = st.selectbox(
        "Scenario",
        FUTURE_SCENARIO_ORDER,
        index=0,
        key="future_projection_scenario",
    )

    future_scenario_df, total_catchments, high_2030, high_2080, delta_high = future_summary_for_scenario(future_counts_df, scenario_name)
    future_scores_scenario = future_scores_df[future_scores_df["scenario"].astype(str) == scenario_name].copy()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("NA Catchments Analyzed", fmt_int(total_catchments))
    c2.metric("High/Extreme Stress (2030)", fmt_int(high_2030))
    c3.metric("High/Extreme Stress (2080)", fmt_int(high_2080))
    c4.metric("Δ High/Extreme (2030→2080)", f"{delta_high:+,}")

    st.markdown("**Water Stress Distribution Across Time Horizons**")
    st.altair_chart(future_share_chart(future_scenario_df), use_container_width=True)

    st.markdown("**Absolute Catchment Counts by Stress Level**")
    st.altair_chart(future_absolute_chart(future_scenario_df), use_container_width=True)

    st.markdown("**Raw Water Stress Score Distribution**")
    selected_future_year = st.selectbox(
        "Select projection year:",
        [2030, 2050, 2080],
        index=0,
        key="future_projection_year",
    )
    hist_source = future_scores_scenario[future_scores_scenario["projection_year"] == selected_future_year].copy()
    st.altair_chart(future_score_histogram(hist_source), use_container_width=True)

    st.markdown("### 📋 Policy Implications")
    st.markdown("- Regions projected to worsen (Southwest, Southern Plains) should require water impact assessments for new data center permits")
    st.markdown("- Regions projected to remain stable (Pacific Northwest, Upper Midwest, New England) are lower-risk candidates for future development")
    st.markdown("- Data centers are long-lived assets (20–30 year lifespans), so siting decisions today lock in environmental impacts for decades")
    st.caption(future_source_note)

else:
    st.subheader("Project notes, methods, and reproducibility")
    render_how_to_read_dashboard("Data notes")

    about_tab, data_tab, methods_tab, glossary_tab = st.tabs(["Project overview", "Data", "Method", "Glossary"])

    with about_tab:
        st.markdown(f"**Research question:** {RESEARCH_QUESTION}")
        st.markdown("**Sub-questions**")
        for i, item in enumerate(SUBQUESTIONS, start=1):
            st.markdown(f"{i}. {item}")

        st.markdown("**What this app adds beyond the raw charts**")
        for item in README_SECTIONS["Project overview"]:
            st.markdown(f"- {item}")

        st.markdown("**Reproducibility checklist**")
        for item in README_SECTIONS["Reproducibility checklist"]:
            st.markdown(f"- {item}")

    with data_tab:
        st.markdown("**Source files used by this app**")
        files_used = pd.DataFrame(DATASET_GUIDE, columns=["File", "Role"])
        st.dataframe(files_used, use_container_width=True, hide_index=True)

        st.markdown("**Current filtered view coverage**")
        coverage = pd.DataFrame(
            {
                "Metric": ["Facilities in current view", "States in current view", "eGRID subregions in current view"],
                "Value": [fmt_int(len(dc_view)), fmt_int(state_view['state_abb'].nunique()), fmt_int(dc_view['egrid_subregion'].nunique())],
            }
        )
        st.dataframe(coverage, use_container_width=True, hide_index=True)

    with methods_tab:
        st.markdown("**Workflow**")
        st.markdown("1. Load facility, county, and state summaries.")
        st.markdown("2. Standardize emissions metrics into lb/MWh, kg/MWh, and tCO₂e/MWh views.")
        st.markdown("3. Link facility locations to eGRID and water-stress indicators.")
        st.markdown("4. Compare concentration, carbon intensity, renewable share, and water stress across geographies.")
        st.markdown("5. Flag facilities in the dual-burden zone for policy discussion.")

        st.markdown("**Important limitations**")
        st.markdown("- Facility square footage is used as a size proxy; it is not direct electricity demand.")
        st.markdown("- Grid carbon intensity is regional and should not be interpreted as an exact facility-specific load profile.")
        st.markdown("- Water stress indicates contextual exposure, not actual on-site water withdrawal.")
        st.markdown("- The dual-burden threshold is a decision aid, not a universal scientific cutoff.")

    with glossary_tab:
        st.markdown("**Carbon intensity** tells you how emissions-heavy the local electricity grid is. Lower is better.")
        st.markdown("**Renewable share** tells you how much of the electricity mix comes from renewable sources. Higher is generally better.")
        st.markdown("**Water stress** comes from WRI Aqueduct categories. Higher stress means greater pressure on local water resources.")
        st.markdown("**Dual burden** means a facility sits in both a water-stressed location and a relatively carbon-intensive grid.")
        st.markdown("**eGRID subregion** is the regional electricity geography used to summarize carbon and power-mix conditions.")


footer_note()
