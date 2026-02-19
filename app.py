import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

st.set_page_config(page_title="GEV Climate Risk Dashboard", layout="wide")

# --- Metric Name Mapping ---
metric_name_map = {
    "Wind_Risk": "Wind Risk",
    "Drought_Risk": "Drought Risk",
    "Wildfire_Risk": "Wildfire Risk",
    "MEAN_low_income_percentage": "Low-Income %",
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

# --- View config ---
view_config = {
    "Wind Risk": {
        "emoji": "🌪️",
        "title": "Wind Risk Explorer",
        "why_title": "Why Wind Risk Matters",
        "why_text": "High winds from tornadoes, hurricanes, and storms threaten homes, power, and safety, often hitting low-income communities hardest. Explore where **wind risk** and **economic vulnerability** intersect to uncover critical patterns.",
        "subtitle": "Visualize the intersection of **wind risk** and **economic vulnerability** across U.S. counties.",
        "risk_col": "Wind_Risk",
        "risk_label": "Wind Risk",
        "filter_label": "Minimum Wind Risk",
        "map_title": "Wind Risk Across U.S. Counties",
        "note": "**Note:** Marker size reflects low-income percentage; color intensity shows wind risk (green = low, red = high).",
        "colorscale": [[0, "green"], [0.5, "yellow"], [1, "red"]],
    },
    "Drought Risk": {
        "emoji": "☀️",
        "title": "Drought Risk Explorer",
        "why_title": "Why Drought Risk Matters",
        "why_text": "Prolonged droughts strain water supplies, agriculture, and livelihoods, disproportionately affecting economically vulnerable communities. Explore where **drought risk** and **economic vulnerability** intersect to uncover critical patterns.",
        "subtitle": "Visualize the intersection of **drought risk** and **economic vulnerability** across U.S. counties.",
        "risk_col": "Drought_Risk",
        "risk_label": "Drought Risk",
        "filter_label": "Minimum Drought Risk",
        "map_title": "Drought Risk Across U.S. Counties",
        "note": "**Note:** Marker size reflects low-income percentage; color intensity shows drought risk (green = low, red = high).",
        "colorscale": [[0, "green"], [0.5, "yellow"], [1, "red"]],
    },
    "Wildfire Risk": {
        "emoji": "🔥",
        "title": "Wildfire Risk Explorer",
        "why_title": "Why Wildfire Risk Matters",
        "why_text": "Wildfires destroy homes, degrade air quality, and displace families, with low-income communities often bearing the greatest burden. Explore where **wildfire risk** and **economic vulnerability** intersect to uncover critical patterns.",
        "subtitle": "Visualize the intersection of **wildfire risk** and **economic vulnerability** across U.S. counties.",
        "risk_col": "Wildfire_Risk",
        "risk_label": "Wildfire Risk",
        "filter_label": "Minimum Wildfire Risk",
        "map_title": "Wildfire Risk Across U.S. Counties",
        "note": "**Note:** Marker size reflects low-income percentage; color intensity shows wildfire risk (green = low, red = high).",
        "colorscale": [[0, "green"], [0.5, "yellow"], [1, "red"]],
    },
}

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

hazard_dfs = {
    "Wind_Risk": wind_df,
    "Drought_Risk": drought_df,
    "Wildfire_Risk": wildfire_df,
}

# --- State options ---
all_states = sorted(health_df["State"].unique().tolist())

# --- Sidebar ---
with st.sidebar:
    st.header("Explore the Data")
    st.markdown("Choose a view")
    view = st.radio(
        "Choose a view",
        ["Wind Risk", "Drought Risk", "Wildfire Risk", "Health & Income"],
        label_visibility="collapsed"
    )

    if view in view_config:
        cfg = view_config[view]
        st.markdown(f"### {cfg['risk_label']} Filters")

        st.markdown("Focus on a State")
        state = st.selectbox("Focus on a State", ["All"] + all_states, label_visibility="collapsed")

        threshold = st.slider(
            cfg["filter_label"],
            min_value=1, max_value=100, value=5,
            help="Set the minimum risk score to display on the map."
        )

        st.markdown("### Search for a County")
        county_search = st.text_input(
            "Enter County Name",
            help="Type a county name to highlight it on the map."
        )

        top_n = st.slider(
            "Number of Counties to Show",
            min_value=5, max_value=955, value=10,
            help="Number of top counties to display in the table below."
        )
    else:
        st.markdown("### Health & Income Filters")
        st.markdown("Focus on a State")
        state = st.selectbox("Focus on a State", ["All"] + all_states, label_visibility="collapsed")

        health_metrics = ["Asthma_Rate____", "Diabetes_Rate____", "Heart_Disease_Rate____", "Life_expectancy__years_"]
        health_metric = st.selectbox(
            "Health Metric",
            health_metrics,
            format_func=lambda m: metric_name_map[m]
        )

        top_n = st.slider(
            "Number of Counties to Show",
            min_value=5, max_value=955, value=10,
            help="Number of top counties to display in the table below."
        )
        threshold = 0
        county_search = ""

# =====================
# MAIN CONTENT
# =====================

# --- Title + Welcome ---
st.markdown("# GEV Climate Risk Dashboard")
st.markdown(
    "Welcome to the GEV Climate Risk Dashboard, a part of the Ten State Project focused on identifying and addressing "
    "climate vulnerability across the United States. This dashboard is a tool for understanding not just where climate "
    "extremes are expected to occur, but where they will likely have the greatest social and economic impact. Vulnerable "
    "communities, especially those with lower incomes and higher health burdens, face steeper challenges in recovery "
    "and resilience. Our goal is to surface those areas clearly and responsibly."
)
st.markdown(
    "Use the options on the left to explore the data by risk type. Each section includes maps, data tables, and summaries "
    "designed to support decision-making and public awareness."
)

# =====================
# HAZARD VIEWS
# =====================
if view in view_config:
    cfg = view_config[view]
    risk_col = cfg["risk_col"]
    risk_label = cfg["risk_label"]
    df = hazard_dfs[risk_col]

    # "Why ___ Matters" section
    st.markdown(f"## {cfg['why_title']}")
    st.markdown(cfg["why_text"])

    # Explorer heading
    st.markdown(f"# {cfg['emoji']} {cfg['title']}")
    st.markdown(cfg["subtitle"])

    # Active filter summary
    st.markdown(f"- **State:** `{state}`")
    st.markdown(f"- **{risk_label} ≥:** `{threshold}`")

    # Filter data
    df_filtered = filter_by_state(df, state)
    filtered = filter_hazard_data(df_filtered, risk_col, threshold)

    # --- Map ---
    st.markdown(f"**{cfg['map_title']}**")

    if filtered.empty:
        st.warning(f"No counties meet the risk threshold of {threshold} for {view}.")
    else:
        fig = go.Figure(go.Scattergeo(
            lon=filtered["Lon"],
            lat=filtered["Lat"],
            text=filtered["County"] + ", " + filtered["State"] + "<br>" + risk_label + ": " + filtered[risk_col].round(1).astype(str),
            marker=dict(
                size=filtered["MEAN_low_income_percentage"].clip(0, 100) * 0.15 + 5,
                color=filtered[risk_col],
                colorscale=cfg["colorscale"],
                showscale=True,
                colorbar=dict(title=risk_label),
                sizemode="diameter",
                sizemin=5
            ),
            name=risk_label
        ))
        fig.update_layout(
            geo=dict(scope="usa", projection_scale=1, center={"lat": 37.1, "lon": -95.7}),
            height=600,
            margin=dict(r=0, l=0, t=30, b=0),
            template="plotly_white",
            font=dict(family="Arial", size=12)
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown(cfg["note"])

        # --- Scatter: Risk vs Low-Income % ---
        st.markdown(f"## {risk_label} vs. Low-Income %")

        scatter_fig = px.scatter(
            filtered,
            x="MEAN_low_income_percentage",
            y=risk_col,
            color="State",
            labels={
                "MEAN_low_income_percentage": "Low-Income %",
                risk_col: risk_label,
            },
            template="plotly_white"
        )
        scatter_fig.update_layout(font=dict(family="Arial", size=12))
        st.plotly_chart(scatter_fig, use_container_width=True)

        # Correlation insight
        valid = filtered[[risk_col, "MEAN_low_income_percentage"]].dropna()
        if len(valid) > 2:
            corr = valid[risk_col].corr(valid["MEAN_low_income_percentage"])
            direction = "higher low-income areas may face higher risk" if corr > 0 else "a weak relationship"
            st.markdown(
                f"**Insight:** The correlation between low-income percentage and {risk_label.lower()} is {corr:.2f}, "
                f"suggesting {direction}. A positive value means higher low-income areas may face higher risk."
            )

        # --- Top N Table ---
        st.markdown(f"## Top {top_n} Counties by {risk_label}")

        top_counties = filtered.sort_values(by=risk_col, ascending=False).head(top_n).copy()

        # County search highlight
        if county_search:
            match = filtered[filtered["County"].str.contains(county_search, case=False, na=False)]
            if not match.empty:
                top_counties = pd.concat([match, top_counties]).drop_duplicates().head(top_n)
            else:
                st.warning(f"No county matching '{county_search}' found with current filters.")

        display_df = top_counties[["County", "State", risk_col, "MEAN_low_income_percentage"]].copy()
        display_df.columns = ["County", "State", risk_label, "Low-Income %"]
        st.dataframe(display_df, use_container_width=True)

        # Download button
        csv = display_df.to_csv(index=False)
        st.download_button(
            label="Download Counties Data",
            data=csv,
            file_name=f"top_{top_n}_{risk_col.lower()}_counties.csv",
            mime="text/csv"
        )

# =====================
# HEALTH & INCOME
# =====================
elif view == "Health & Income":
    st.markdown("## Why Health & Income Matters")
    st.markdown(
        "Understanding the link between **economic hardship** and **health outcomes** is critical for building healthier, "
        "more resilient communities. Explore how low-income populations face compounded health challenges across U.S. counties."
    )

    st.markdown("# 🏥 Health & Income Explorer")
    st.markdown("Visualize the intersection of **health metrics** and **economic vulnerability** across U.S. counties.")

    st.markdown(f"- **State:** `{state}`")
    st.markdown(f"- **Metric:** `{metric_name_map[health_metric]}`")

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
        hist.update_xaxes(title_text="Low-Income %")
        st.plotly_chart(hist, use_container_width=True)

        # Scatter: Health metric vs Low-Income %
        health_df_filtered = health_df_filtered.copy()
        health_df_filtered[health_metric] = pd.to_numeric(health_df_filtered[health_metric], errors='coerce')
        health_valid = health_df_filtered.dropna(subset=[health_metric])

        st.markdown(f"## {metric_name_map[health_metric]} vs. Low-Income %")

        scatter_fig = px.scatter(
            health_valid,
            x="MEAN_low_income_percentage",
            y=health_metric,
            color="State",
            labels={
                "MEAN_low_income_percentage": "Low-Income %",
                health_metric: metric_name_map[health_metric],
            },
            template="plotly_white"
        )
        scatter_fig.update_layout(font=dict(family="Arial", size=12))
        st.plotly_chart(scatter_fig, use_container_width=True)

        # Correlation insight
        valid = health_valid[[health_metric, "MEAN_low_income_percentage"]].dropna()
        if len(valid) > 2:
            corr = valid[health_metric].corr(valid["MEAN_low_income_percentage"])
            direction = "higher low-income areas may face worse outcomes" if corr > 0 else "a weak relationship"
            st.markdown(
                f"**Insight:** The correlation between low-income percentage and {metric_name_map[health_metric].lower()} is {corr:.2f}, "
                f"suggesting {direction}. A positive value means higher low-income areas may face worse health outcomes."
            )

        # Top N table
        top = health_valid.sort_values(by=health_metric, ascending=False).head(top_n)

        st.markdown(f"## Top {top_n} Counties by {metric_name_map[health_metric]}")

        if top.empty:
            st.warning(f"No data available for {metric_name_map[health_metric]}.")
        else:
            display_df = top[["County", "State", health_metric, "MEAN_low_income_percentage"]].copy()
            display_df.columns = ["County", "State", metric_name_map[health_metric], "Low-Income %"]
            st.dataframe(display_df, use_container_width=True)

            csv = display_df.to_csv(index=False)
            st.download_button(
                label="Download Counties Data",
                data=csv,
                file_name=f"top_{top_n}_{health_metric.lower()}_counties.csv",
                mime="text/csv"
            )
