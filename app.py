import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from constants import metric_name_map, wind_url, drought_url, wildfire_url, census_url, health_url
from data_loader import load_hazard, load_census, load_health_data, filter_hazard_data, filter_by_state
from views import hazard_map_view

st.set_page_config(page_title="GEV Analysis Dashboard", layout="wide")

# --- Load data ---
with st.spinner("Loading data..."):
    wind_df = load_hazard(wind_url, "Wind_Risk")
    drought_df = load_hazard(drought_url, "Drought_Risk")
    wildfire_df = load_hazard(wildfire_url, "Wildfire_Risk")
    census_df = load_census(census_url)
    health_df = load_health_data(health_url)

# --- Compute Key Findings ---
asthma_finding = "No health data available."
if not health_df.empty:
    health_df["Asthma_Rate____"] = pd.to_numeric(health_df["Asthma_Rate____"], errors="coerce")
    top_asthma = health_df.sort_values(by="Asthma_Rate____", ascending=False).head(10)
    if len(top_asthma) >= 2:
        c1, c2 = top_asthma.iloc[0], top_asthma.iloc[1]
        asthma_finding = (
            f"For example, {c1['County']}, {c1['State']} has an asthma rate of {c1['Asthma_Rate____']:.1f}% "
            f"and a low-income population percentage of {c1['MEAN_low_income_percentage']:.1f}%, "
            f"while {c2['County']}, {c2['State']} shows an asthma rate of {c2['Asthma_Rate____']:.1f}% "
            f"with a low-income percentage of {c2['MEAN_low_income_percentage']:.1f}%. "
            "These counties rank among the top 10 for asthma prevalence, indicating a strong correlation "
            "between economic disadvantage and respiratory health challenges."
        )

wildfire_finding = "No wildfire data available with risk >= 50."
high_wildfire = wildfire_df[wildfire_df["Wildfire_Risk"] >= 50]
if not high_wildfire.empty:
    top_wildfire = high_wildfire.sort_values(by="Wildfire_Risk", ascending=False).head(10)
    if len(top_wildfire) >= 2:
        c1, c2 = top_wildfire.iloc[0], top_wildfire.iloc[1]
        max_risk = top_wildfire["Wildfire_Risk"].max()
        avg_low_income = top_wildfire["MEAN_low_income_percentage"].mean()
        wildfire_finding = (
            f"Counties like {c1['County']}, {c1['State']} and {c2['County']}, {c2['State']}, "
            f"which have low-income populations around {avg_low_income:.1f}%, also face elevated wildfire risks, "
            f"with scores reaching up to {max_risk:.1f}. This suggests a compounded vulnerability in these areas."
        )

# --- State options ---
states = ["All"] + sorted(health_df["State"].unique().tolist())

# --- Title ---
st.title("GEV Analysis Dashboard")

# --- Introduction ---
with st.expander("Introduction", expanded=False):
    st.write(
        "The 'Ten State Project' is a research initiative focused on evaluating climate risk vulnerabilities "
        "across ten U.S. states, emphasizing the interplay between environmental hazards, socioeconomic challenges, "
        "and health outcomes. By integrating advanced climate modeling with socioeconomic and health data, the project "
        "identifies regions most susceptible to extreme weather events like droughts, wildfires, and windstorms, "
        "particularly in low-income and marginalized communities."
    )
    st.write(
        "Our project, the 'GEV Analysis Dashboard,' builds on the 'Ten State Project' by offering an interactive tool "
        "to explore these vulnerabilities at the county level across the U.S. We utilize datasets from AT&T Climate "
        "Resiliency, covering drought, wildfire, and wind risks, alongside U.S. Census Bureau data on socioeconomic "
        "factors and health metrics like asthma and diabetes rates."
    )

# --- Sidebar ---
with st.sidebar:
    st.header("Filters")
    state = st.selectbox("Select State", states, index=0)
    st.header("Navigation")
    view = st.radio("View", ["Hazard Map", "Community Indicators", "Health & Income"])

# --- Filter data by state ---
wind_df_f = filter_by_state(wind_df, state)
drought_df_f = filter_by_state(drought_df, state)
wildfire_df_f = filter_by_state(wildfire_df, state)

# =====================
# HAZARD MAP VIEW
# =====================
if view == "Hazard Map":
    hazard_map_view(wind_df_f, drought_df_f, wildfire_df_f, state, metric_name_map)

# =====================
# COMMUNITY INDICATORS
# =====================
elif view == "Community Indicators":
    community_metrics = [
        "Identified as disadvantaged", "Energy burden", "PM2.5 in the air",
        "Current asthma among adults aged greater than or equal to 18 years",
        "Share of properties at risk of fire in 30 years", "Total population"
    ]
    raw_metric = st.selectbox(
        "Select Metric",
        community_metrics,
        format_func=lambda m: metric_name_map[m],
        index=1
    )
    top_n = st.slider("Top N Counties", 5, 50, 10, 5)

    census_df_filtered = filter_by_state(census_df, state)
    st.subheader(f"Community Disadvantage & Demographics ({state if state != 'All' else 'All States'})")
    st.caption("Note: Explore metrics like energy burden or air quality. Higher values indicate greater vulnerability. Adjust 'Top N' to see more counties.")

    subset = census_df_filtered[census_df_filtered[raw_metric].notna()].copy()
    if raw_metric == "Identified as disadvantaged":
        subset[raw_metric] = subset[raw_metric].astype(str).str.lower() == "true"
        subset = subset[subset[raw_metric] == True]
    top = subset.sort_values(by=raw_metric, ascending=False).head(top_n)

    if top.empty:
        st.warning(f"No data available for {metric_name_map[raw_metric]}.")
    else:
        if raw_metric != "Identified as disadvantaged":
            top[raw_metric] = pd.to_numeric(top[raw_metric], errors="coerce")
            top = top.dropna(subset=[raw_metric])

        display_cols = ["County", "State", raw_metric]
        if "Total population" in top.columns:
            display_cols.append("Total population")
        display_df = top[display_cols].copy()
        display_df.columns = [metric_name_map.get(c, c) for c in display_df.columns]
        st.dataframe(display_df, use_container_width=True, hide_index=True)

        if raw_metric != "Identified as disadvantaged":
            fig = px.bar(
                top, x="County", y=raw_metric, color="State",
                title=f"{metric_name_map[raw_metric]} by County",
                color_discrete_sequence=["#2D584A"],
                template="plotly_white"
            )
            fig.update_layout(xaxis_tickangle=-45, font=dict(family="Arial", size=12))
            fig.update_yaxes(title_text=metric_name_map[raw_metric])
            st.plotly_chart(fig, use_container_width=True)

# =====================
# HEALTH & INCOME
# =====================
elif view == "Health & Income":
    health_metrics = ["Asthma_Rate____", "Diabetes_Rate____", "Heart_Disease_Rate____", "Life_expectancy__years_"]
    raw_metric = st.selectbox(
        "Select Health Metric",
        health_metrics,
        format_func=lambda m: metric_name_map[m]
    )

    health_df_filtered = filter_by_state(health_df, state)

    if health_df_filtered.empty:
        st.warning(f"No health data available for {state if state != 'All' else 'the selected states'}.")
    else:
        # Histogram
        hist = px.histogram(
            health_df_filtered, x="MEAN_low_income_percentage", nbins=30,
            title=f"Low-Income Distribution Across Counties in {state if state != 'All' else 'All States'}",
            color_discrete_sequence=["#C0C0C0"],
            template="plotly_white"
        )
        hist.update_layout(font=dict(family="Arial", size=12))
        hist.update_xaxes(title_text=metric_name_map["MEAN_low_income_percentage"])
        st.plotly_chart(hist, use_container_width=True)

        # Top 10 bar
        health_df_filtered = health_df_filtered.copy()
        health_df_filtered[raw_metric] = pd.to_numeric(health_df_filtered[raw_metric], errors="coerce")
        top = health_df_filtered.sort_values(by=raw_metric, ascending=False).head(10)
        top = top.dropna(subset=[raw_metric])

        st.subheader(f"Top 10 Counties by {metric_name_map[raw_metric]} ({state if state != 'All' else 'All States'})")

        if top.empty:
            st.warning(f"No data available for {metric_name_map[raw_metric]}.")
        else:
            bar = px.bar(
                top, x="County", y=raw_metric, color="State",
                title=f"Top 10 Counties for {metric_name_map[raw_metric]}",
                hover_data=["MEAN_low_income_percentage"],
                color_discrete_sequence=["#2D584A"],
                template="plotly_white"
            )
            bar.update_layout(font=dict(family="Arial", size=12))
            bar.update_yaxes(title_text=metric_name_map[raw_metric])
            st.plotly_chart(bar, use_container_width=True)

            display_df = top[["County", "State", raw_metric, "MEAN_low_income_percentage"]].copy()
            display_df.columns = ["County", "State", metric_name_map[raw_metric], metric_name_map["MEAN_low_income_percentage"]]
            st.dataframe(display_df, use_container_width=True, hide_index=True)

# --- Key Findings ---
st.divider()
st.subheader("Key Findings")
st.markdown(f"**Health and Income Disparities:** {asthma_finding}")
st.markdown(f"**Wildfire Risk Patterns:** {wildfire_finding}")
