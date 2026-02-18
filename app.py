import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="GEV Analysis Dashboard", layout="wide")

# --- Metric Name Mapping ---
metric_name_map = {
    "Wind_Risk": "Wind Risk Score",
    "Drought_Risk": "Drought Risk Score",
    "Wildfire_Risk": "Wildfire Risk Score",
    "MEAN_low_income_percentage": "Low-Income Population (%)",
    "Identified as disadvantaged": "Disadvantaged Community",
    "Energy burden": "Energy Burden (%)",
    "PM2.5 in the air": "PM2.5 Air Pollution (µg/m³)",
    "Current asthma among adults aged greater than or equal to 18 years": "Adult Asthma Rate (%)",
    "Share of properties at risk of fire in 30 years": "Properties at Fire Risk (%)",
    "Total population": "Total Population",
    "Asthma_Rate____": "Asthma Rate (%)",
    "Diabetes_Rate____": "Diabetes Rate (%)",
    "Heart_Disease_Rate____": "Heart Disease Rate (%)",
    "Life_expectancy__years_": "Life Expectancy (Years)"
}

# --- URLs ---
wind_url = "https://undivideprojectdata.blob.core.windows.net/gev/wind.csv?sp=r&st=2025-05-29T03:41:03Z&se=2090-05-29T11:41:03Z&spr=https&sv=2024-11-04&sr=b&sig=iHyfpuXMWL7L59fxz1X8lcgcM4Wiqlaf2ybA%2FTX14Bg%3D"
drought_url = "https://undivideprojectdata.blob.core.windows.net/gev/drought_analysis.csv?sp=r&st=2025-05-29T03:49:51Z&se=2090-05-29T11:49:51Z&spr=https&sv=2024-11-04&sr=b&sig=UCvT2wK1gzScGOYyK0WWAwtWZSmmVf3T1HGjyOkaeZk%3D"
wildfire_url = "https://undivideprojectdata.blob.core.windows.net/gev/wildfire.csv?sp=r&st=2025-05-29T03:04:38Z&se=2090-05-29T11:04:38Z&spr=https&sv=2024-11-04&sr=b&sig=Vd%2FhCXRq3gQF2WmdI3wjoksdl0nPTmCWUSrYodobDyw%3D"
census_url = "https://undivideprojectdata.blob.core.windows.net/gev/1.0-communities.csv?sp=r&st=2025-05-30T23:23:50Z&se=2090-05-31T07:23:50Z&spr=https&sv=2024-11-04&sr=b&sig=qC7ouZhUV%2BOMrZJ4tvHslvQeKUdXdA15arv%2FE2pPxEI%3D"
health_url = "https://undivideprojectdata.blob.core.windows.net/gev/health.csv?sp=r&st=2025-05-31T00:13:59Z&se=2090-05-31T08:13:59Z&spr=https&sv=2024-11-04&sr=b&sig=8epnZK%2FXbnblTCiYlmtuYHgBy43yxCHTtS7FqLu134k%3D"

# --- Loaders ---
@st.cache_data(show_spinner=False)
def load_hazard(url, risk_col):
    try:
        df = pd.read_csv(url, usecols=["CF", "SF", "Latitude", "Longitude", "MEAN_low_income_percentage", "midcent_median_10yr"])
        df = df.rename(columns={"CF": "County", "SF": "State", "Latitude": "Lat", "Longitude": "Lon",
                                "MEAN_low_income_percentage": "MEAN_low_income_percentage", "midcent_median_10yr": risk_col})
        df["County"] = df["County"].str.title()
        df["State"] = df["State"].str.title()
        df[risk_col] = pd.to_numeric(df[risk_col], errors='coerce')
        df["MEAN_low_income_percentage"] = pd.to_numeric(df["MEAN_low_income_percentage"], errors='coerce')
        return df.dropna(subset=["Lat", "Lon", risk_col])
    except Exception as e:
        st.error(f"Error loading data from {url}: {e}")
        return pd.DataFrame()

@st.cache_data(show_spinner=False)
def load_census():
    try:
        df = pd.read_csv(census_url)
        df.columns = df.columns.str.strip()
        df = df.rename(columns={"County Name": "County", "State/Territory": "State"})
        df["County"] = df["County"].str.title()
        df["State"] = df["State"].str.title()
        return df
    except Exception as e:
        st.error(f"Error loading census data: {e}")
        return pd.DataFrame()

@st.cache_data(show_spinner=False)
def load_health_data():
    try:
        df = pd.read_csv(health_url)
        df.columns = df.columns.str.strip()
        df = df.rename(columns={"CF": "County", "SF": "State"})
        df["County"] = df["County"].str.title()
        df["State"] = df["State"].str.title()
        df["MEAN_low_income_percentage"] = pd.to_numeric(df["MEAN_low_income_percentage"], errors='coerce')
        df["Asthma_Rate____"] = pd.to_numeric(df["Asthma_Rate____"], errors='coerce')
        return df.dropna(subset=["MEAN_low_income_percentage"])
    except Exception as e:
        st.error(f"Error loading health data: {e}")
        return pd.DataFrame()

def filter_hazard_data(df, risk_col, threshold):
    filtered_df = df[df[risk_col] >= threshold].copy()
    filtered_df[risk_col] = pd.to_numeric(filtered_df[risk_col], errors='coerce')
    return filtered_df.dropna(subset=[risk_col])

def filter_by_state(df, state):
    if state == "All":
        return df
    return df[df["State"] == state]

# --- Load data ---
with st.spinner("Loading data..."):
    wind_df = load_hazard(wind_url, "Wind_Risk")
    drought_df = load_hazard(drought_url, "Drought_Risk")
    wildfire_df = load_hazard(wildfire_url, "Wildfire_Risk")
    census_df = load_census()
    health_df = load_health_data()

# --- Compute Key Findings ---
# Asthma and Low-Income: Top counties across all states
if not health_df.empty:
    top_asthma = health_df.sort_values(by="Asthma_Rate____", ascending=False).head(10)
    if len(top_asthma) >= 2:
        county1, county2 = top_asthma.iloc[0], top_asthma.iloc[1]
        asthma_finding = (
            f"For example, {county1['County']}, {county1['State']} has an asthma rate of {county1['Asthma_Rate____']:.1f}% "
            f"and a low-income population percentage of {county1['MEAN_low_income_percentage']:.1f}%, "
            f"while {county2['County']}, {county2['State']} shows an asthma rate of {county2['Asthma_Rate____']:.1f}% "
            f"with a low-income percentage of {county2['MEAN_low_income_percentage']:.1f}%. "
            "These counties rank among the top 10 for asthma prevalence, indicating a strong correlation "
            "between economic disadvantage and respiratory health challenges. Users can filter by state "
            "and select 'Asthma Rate (%)' to explore these patterns."
        )
    else:
        asthma_finding = "Insufficient data to identify top asthma counties across states."
else:
    asthma_finding = "No health data available."

# Wildfire Risk: Top counties across all states with risk >= 50
high_wildfire = wildfire_df[wildfire_df["Wildfire_Risk"] >= 50]
if not high_wildfire.empty:
    top_wildfire = high_wildfire.sort_values(by="Wildfire_Risk", ascending=False).head(10)
    if len(top_wildfire) >= 2:
        county1, county2 = top_wildfire.iloc[0], top_wildfire.iloc[1]
        max_risk = top_wildfire["Wildfire_Risk"].max()
        avg_low_income = top_wildfire["MEAN_low_income_percentage"].mean()
        wildfire_finding = (
            f"Counties like {county1['County']}, {county1['State']} and {county2['County']}, {county2['State']}, "
            f"which have low-income populations around {avg_low_income:.1f}%, also face elevated wildfire risks, "
            f"with scores reaching up to {max_risk:.1f}. This suggests a compounded vulnerability in these areas. "
            "Users can filter by state, choose 'Wildfire Risk,' and set the risk threshold to 50 to see similar results."
        )
    else:
        wildfire_finding = "Insufficient data to identify high wildfire risk counties."
else:
    wildfire_finding = "No wildfire data available with risk >= 50."

# --- State options for dropdown ---
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
        "particularly in low-income and marginalized communities. It aims to raise awareness among local populations "
        "about the compounded risks they face, such as increased asthma prevalence due to environmental stressors, "
        "and to provide data-driven insights for building resilience. The project uses tools like the Generalized "
        "Extreme Value (GEV) model to forecast future climate risks and overlays this with health and economic "
        "indicators to highlight disparities, enabling targeted interventions for at-risk areas."
    )
    st.write(
        "Our project, the 'GEV Analysis Dashboard,' builds on the 'Ten State Project' by offering an interactive "
        "tool to explore these vulnerabilities at the county level across the U.S. We utilize datasets from AT&T "
        "Climate Resiliency, covering drought, wildfire, and wind risks, alongside U.S. Census Bureau data on "
        "socioeconomic factors and health metrics like asthma and diabetes rates. The dashboard allows users to "
        "filter by state, hazard type, and health indicators, providing a granular view of how climate risks "
        "intersect with economic and health challenges. By making this data accessible, we aim to empower community "
        "leaders, policymakers, and residents to address climate risks equitably, bridging the gap between complex "
        "data and actionable insights for vulnerable populations."
    )

# --- Sidebar ---
with st.sidebar:
    st.header("Filters")
    state = st.selectbox("Select State", states, index=0)

    st.header("Navigation")
    view = st.radio("View", ["Hazard Map", "Community Indicators", "Health & Income"])

# --- Hazard constants ---
colors = {"Wind Risk": "#2D584A", "Drought Risk": "#759B90", "Wildfire Risk": "#000000"}
hazard_raw_map = {"Wind Risk": "Wind_Risk", "Drought Risk": "Drought_Risk", "Wildfire Risk": "Wildfire_Risk"}

# =====================
# HAZARD MAP VIEW
# =====================
if view == "Hazard Map":
    hazards = st.multiselect(
        "Select Hazard Types",
        ["Wind Risk", "Drought Risk", "Wildfire Risk"],
        default=["Wind Risk"]
    )
    threshold = st.slider("Risk Threshold", 0.0, 50.0, 5.0, 1.0)

    st.subheader(f"Hazard Exposure Across Counties ({state if state != 'All' else 'All States'})")
    st.caption("Note: Risk reflects 10-year median projections. Marker size shows low-income %, color shows hazard type. Adjust threshold or select multiple hazards to compare.")

    wind_df_filtered = filter_by_state(wind_df, state)
    drought_df_filtered = filter_by_state(drought_df, state)
    wildfire_df_filtered = filter_by_state(wildfire_df, state)

    fig = go.Figure()
    for h in hazards:
        risk_col = hazard_raw_map[h]
        df = wind_df_filtered if h == "Wind Risk" else drought_df_filtered if h == "Drought Risk" else wildfire_df_filtered
        filtered = filter_hazard_data(df, risk_col, threshold)
        if filtered.empty:
            st.warning(f"No counties meet the risk threshold for {metric_name_map[risk_col]} in {state if state != 'All' else 'the selected states'}.")
            continue
        fig.add_trace(go.Scattergeo(
            lon=filtered["Lon"],
            lat=filtered["Lat"],
            text=filtered["County"] + ", " + filtered["State"] + "<br>" + metric_name_map[risk_col] + ": " + filtered[risk_col].astype(str),
            marker=dict(
                size=filtered["MEAN_low_income_percentage"].clip(0, 100) * 0.15 + 5,
                color=colors[h],
                showscale=False,
                sizemode="diameter",
                sizemin=5
            ),
            name=metric_name_map[risk_col]
        ))
    fig.update_layout(
        geo=dict(scope="usa", projection_scale=1, center={"lat": 37.1, "lon": -95.7}),
        height=600,
        margin=dict(r=0, l=0, t=30, b=0),
        template="plotly_white",
        font=dict(family="Arial", size=12)
    )
    st.plotly_chart(fig, use_container_width=True)

    # Top 10 charts
    st.subheader(f"Top 10 Counties by Risk ({state if state != 'All' else 'All States'})")
    for h in hazards:
        risk_col = hazard_raw_map[h]
        df = wind_df_filtered if h == "Wind Risk" else drought_df_filtered if h == "Drought Risk" else wildfire_df_filtered
        filtered = filter_hazard_data(df, risk_col, threshold)
        if not filtered.empty:
            top_10 = filtered.sort_values(by=risk_col, ascending=False).head(10).copy()
            top_10[risk_col] = pd.to_numeric(top_10[risk_col], errors='coerce')
            top_10["MEAN_low_income_percentage"] = pd.to_numeric(top_10["MEAN_low_income_percentage"], errors='coerce')
            top_10_clean = top_10.dropna(subset=[risk_col, "MEAN_low_income_percentage"])

            if top_10_clean.empty:
                st.warning(f"No valid data to plot for {metric_name_map[risk_col]} after cleaning.")
            else:
                hist_fig = px.histogram(
                    top_10_clean,
                    x=risk_col,
                    nbins=10,
                    title=f"Distribution of {metric_name_map[risk_col]} for Top 10 Counties",
                    color_discrete_sequence=[colors[h]],
                    template="plotly_white"
                )
                hist_fig.update_layout(
                    xaxis_title=metric_name_map[risk_col],
                    yaxis_title="Number of Counties",
                    font=dict(family="Arial", size=12)
                )
                st.plotly_chart(hist_fig, use_container_width=True)

                bar_fig = go.Figure()
                bar_fig.add_trace(go.Bar(
                    x=top_10_clean["County"],
                    y=top_10_clean[risk_col],
                    name=metric_name_map[risk_col],
                    marker_color=colors[h]
                ))
                bar_fig.add_trace(go.Bar(
                    x=top_10_clean["County"],
                    y=top_10_clean["MEAN_low_income_percentage"],
                    name=metric_name_map["MEAN_low_income_percentage"],
                    marker_color="#C0C0C0"
                ))
                bar_fig.update_layout(
                    title=f"Top 10 Counties: {metric_name_map[risk_col]} vs {metric_name_map['MEAN_low_income_percentage']}",
                    barmode="group",
                    xaxis_title="County",
                    yaxis_title="Value",
                    template="plotly_white",
                    font=dict(family="Arial", size=12),
                    xaxis_tickangle=-45
                )
                st.plotly_chart(bar_fig, use_container_width=True)
        else:
            st.warning(f"No data to display for {metric_name_map[hazard_raw_map[h]]} in {state if state != 'All' else 'the selected states'}.")

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
        subset[raw_metric] = subset[raw_metric].astype(str).str.lower() == 'true'
        subset = subset[subset[raw_metric] == True]
    top = subset.sort_values(by=raw_metric, ascending=False).head(top_n)

    if top.empty:
        st.warning(f"No data available for {metric_name_map[raw_metric]} in {state if state != 'All' else 'the selected states'}.")
    else:
        if raw_metric != "Identified as disadvantaged":
            top = top.copy()
            top[raw_metric] = pd.to_numeric(top[raw_metric], errors='coerce')
            top = top.dropna(subset=[raw_metric])
        display_cols = ["County", "State", raw_metric]
        if "Total population" in top.columns:
            display_cols.append("Total population")
        display_df = top[display_cols].copy()
        display_df.columns = [col if col not in metric_name_map else metric_name_map[col] for col in display_df.columns]
        st.dataframe(display_df, use_container_width=True, hide_index=True)

        if raw_metric != "Identified as disadvantaged":
            fig = px.bar(
                top, x="County", y=raw_metric, color="State",
                title=f"{metric_name_map[raw_metric]} by County in {state if state != 'All' else 'All States'}",
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
        # Income histogram
        hist = px.histogram(
            health_df_filtered,
            x="MEAN_low_income_percentage",
            nbins=30,
            title=f"Low-Income Distribution Across Counties in {state if state != 'All' else 'All States'}",
            color_discrete_sequence=["#C0C0C0"],
            template="plotly_white"
        )
        hist.update_layout(font=dict(family="Arial", size=12))
        hist.update_xaxes(title_text=metric_name_map["MEAN_low_income_percentage"])
        st.plotly_chart(hist, use_container_width=True)

        # Top 10 by health metric
        health_df_filtered = health_df_filtered.copy()
        health_df_filtered[raw_metric] = pd.to_numeric(health_df_filtered[raw_metric], errors='coerce')
        top = health_df_filtered.sort_values(by=raw_metric, ascending=False).head(10)
        top = top.dropna(subset=[raw_metric])

        st.subheader(f"Top 10 Counties by {metric_name_map[raw_metric]} in {state if state != 'All' else 'All States'}")

        if top.empty:
            st.warning(f"No data available for {metric_name_map[raw_metric]} in {state if state != 'All' else 'the selected states'}.")
        else:
            bar = px.bar(
                top,
                x="County",
                y=raw_metric,
                color="State",
                title=f"Top 10 Counties for {metric_name_map[raw_metric]} in {state if state != 'All' else 'All States'}",
                hover_data=["MEAN_low_income_percentage"],
                color_discrete_sequence=["#2D584A"],
                template="plotly_white"
            )
            bar.update_layout(font=dict(family="Arial", size=12))
            bar.update_yaxes(title_text=metric_name_map[raw_metric])
            bar.update_traces(hovertemplate="County: %{x}<br>" + metric_name_map[raw_metric] + ": %{y}<br>" + metric_name_map["MEAN_low_income_percentage"] + ": %{customdata}")
            st.plotly_chart(bar, use_container_width=True)

            display_df = top[["County", "State", raw_metric, "MEAN_low_income_percentage"]].copy()
            display_df.columns = ["County", "State", metric_name_map[raw_metric], metric_name_map["MEAN_low_income_percentage"]]
            st.dataframe(display_df, use_container_width=True, hide_index=True)

# --- Key Findings ---
st.divider()
st.subheader("Key Findings")
st.markdown(f"**Health and Income Disparities:** {asthma_finding}")
st.markdown(f"**Wildfire Risk Patterns:** {wildfire_finding}")
