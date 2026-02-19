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

# --- View config ---
view_config = {
    "Wind Risk": {
        "emoji": "🌪️",
        "title": "Wind Risk Explorer",
        "intro": "High winds from tornadoes, hurricanes, and storms threaten homes, power, and safety, often hitting low-income communities hardest. Explore where **wind risk** and **economic vulnerability** intersect to uncover critical patterns.",
        "subtitle": "Visualize the intersection of **wind risk** and **economic vulnerability** across U.S. counties.",
        "risk_col": "Wind_Risk",
        "filter_label": "Minimum Wind Risk",
        "map_title": "Wind Risk Across U.S. Counties",
        "colorscale": "OrRd",
    },
    "Drought Risk": {
        "emoji": "☀️",
        "title": "Drought Risk Explorer",
        "intro": "Prolonged droughts strain water supplies, agriculture, and livelihoods, disproportionately affecting economically vulnerable communities. Explore where **drought risk** and **economic vulnerability** intersect to uncover critical patterns.",
        "subtitle": "Visualize the intersection of **drought risk** and **economic vulnerability** across U.S. counties.",
        "risk_col": "Drought_Risk",
        "filter_label": "Minimum Drought Risk",
        "map_title": "Drought Risk Across U.S. Counties",
        "colorscale": "YlOrBr",
    },
    "Wildfire Risk": {
        "emoji": "🔥",
        "title": "Wildfire Risk Explorer",
        "intro": "Wildfires destroy homes, degrade air quality, and displace families, with low-income communities often bearing the greatest burden. Explore where **wildfire risk** and **economic vulnerability** intersect to uncover critical patterns.",
        "subtitle": "Visualize the intersection of **wildfire risk** and **economic vulnerability** across U.S. counties.",
        "risk_col": "Wildfire_Risk",
        "filter_label": "Minimum Wildfire Risk",
        "map_title": "Wildfire Risk Across U.S. Counties",
        "colorscale": "Reds",
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

    # Hazard views share similar sidebar filters
    if view in view_config:
        cfg = view_config[view]
        st.markdown(f"### {view} Filters")

        st.markdown("Focus on a State")
        state = st.selectbox("Focus on a State", ["All"] + all_states, label_visibility="collapsed")

        threshold = st.slider(
            cfg["filter_label"],
            min_value=0, max_value=100, value=5,
            help="Set the minimum risk score to display on the map."
        )

        st.markdown("### Search for a County")
        county_search = st.text_input(
            "Enter County Name",
            help="Type a county name to highlight it on the map."
        )

        top_n = st.slider(
            "Number of Counties to Show",
            min_value=5, max_value=50, value=10,
            help="Number of top counties to display in the charts below."
        )
    else:
        # Health & Income sidebar
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
            min_value=5, max_value=50, value=10,
            help="Number of top counties to display in the charts below."
        )
        threshold = 0
        county_search = ""

# =====================
# HAZARD VIEWS (Wind / Drought / Wildfire)
# =====================
if view in view_config:
    cfg = view_config[view]
    risk_col = cfg["risk_col"]
    df = hazard_dfs[risk_col]

    # Intro paragraph
    st.markdown(cfg["intro"])

    # Big emoji + title
    st.markdown(f"# {cfg['emoji']} {cfg['title']}")
    st.markdown(cfg["subtitle"])

    # Active filter summary
    st.markdown(f"- **State:** `{state}`")
    st.markdown(f"- **{cfg['filter_label'].replace('Minimum ', '')} ≥:** `{threshold}`")

    # Filter data
    df_filtered = filter_by_state(df, state)
    filtered = filter_hazard_data(df_filtered, risk_col, threshold)

    # County search highlight
    if county_search:
        match = filtered[filtered["County"].str.contains(county_search, case=False, na=False)]
        if match.empty:
            st.warning(f"No county matching '{county_search}' found with current filters.")

    # --- Map ---
    st.markdown(f"**{cfg['map_title']}**")

    if filtered.empty:
        st.warning(f"No counties meet the risk threshold of {threshold} for {view}.")
    else:
        fig = go.Figure(go.Scattergeo(
            lon=filtered["Lon"],
            lat=filtered["Lat"],
            text=filtered["County"] + ", " + filtered["State"] + "<br>" + metric_name_map[risk_col] + ": " + filtered[risk_col].round(1).astype(str),
            marker=dict(
                size=filtered["MEAN_low_income_percentage"].clip(0, 100) * 0.15 + 5,
                color=filtered[risk_col],
                colorscale=cfg["colorscale"],
                showscale=True,
                colorbar=dict(title=view),
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

        # --- Top N bar chart ---
        top_counties = filtered.sort_values(by=risk_col, ascending=False).head(top_n).copy()
        top_counties[risk_col] = pd.to_numeric(top_counties[risk_col], errors='coerce')
        top_counties["MEAN_low_income_percentage"] = pd.to_numeric(top_counties["MEAN_low_income_percentage"], errors='coerce')
        top_clean = top_counties.dropna(subset=[risk_col, "MEAN_low_income_percentage"])

        if not top_clean.empty:
            st.markdown(f"### Top {top_n} Counties by {metric_name_map[risk_col]}")

            bar_fig = go.Figure()
            bar_fig.add_trace(go.Bar(
                x=top_clean["County"] + ", " + top_clean["State"],
                y=top_clean[risk_col],
                name=metric_name_map[risk_col],
                marker_color="#2D584A"
            ))
            bar_fig.add_trace(go.Bar(
                x=top_clean["County"] + ", " + top_clean["State"],
                y=top_clean["MEAN_low_income_percentage"],
                name=metric_name_map["MEAN_low_income_percentage"],
                marker_color="#C0C0C0"
            ))
            bar_fig.update_layout(
                title=f"Top {top_n} Counties: {metric_name_map[risk_col]} vs {metric_name_map['MEAN_low_income_percentage']}",
                barmode="group",
                xaxis_title="County",
                yaxis_title="Value",
                template="plotly_white",
                font=dict(family="Arial", size=12),
                xaxis_tickangle=-45
            )
            st.plotly_chart(bar_fig, use_container_width=True)

            # Distribution histogram
            hist_fig = px.histogram(
                top_clean,
                x=risk_col,
                nbins=10,
                title=f"Distribution of {metric_name_map[risk_col]} for Top {top_n} Counties",
                color_discrete_sequence=["#2D584A"],
                template="plotly_white"
            )
            hist_fig.update_layout(
                xaxis_title=metric_name_map[risk_col],
                yaxis_title="Number of Counties",
                font=dict(family="Arial", size=12)
            )
            st.plotly_chart(hist_fig, use_container_width=True)

            # Data table
            st.markdown(f"### County Data")
            display_df = top_clean[["County", "State", risk_col, "MEAN_low_income_percentage"]].copy()
            display_df.columns = ["County", "State", metric_name_map[risk_col], metric_name_map["MEAN_low_income_percentage"]]
            table_html = "<table style='border-collapse: collapse; width: 100%;'>"
            table_html += "<thead><tr>"
            for col in display_df.columns:
                table_html += f"<th style='font-family: Arial; border: 1px solid black; padding: 5px;'>{col}</th>"
            table_html += "</tr></thead><tbody>"
            for i in range(len(display_df)):
                table_html += "<tr>"
                for col in display_df.columns:
                    val = display_df.iloc[i][col]
                    if isinstance(val, float):
                        val = f"{val:.1f}"
                    table_html += f"<td style='font-family: Arial; border: 1px solid black; padding: 5px;'>{val}</td>"
                table_html += "</tr>"
            table_html += "</tbody></table>"
            st.markdown(table_html, unsafe_allow_html=True)

# =====================
# HEALTH & INCOME
# =====================
elif view == "Health & Income":
    st.markdown("Understanding the link between **economic hardship** and **health outcomes** is critical for building healthier, more resilient communities. Explore how low-income populations face compounded health challenges across U.S. counties.")

    st.markdown("# 🏥 Health & Income Explorer")
    st.markdown("Visualize the intersection of **health metrics** and **economic vulnerability** across U.S. counties.")

    st.markdown(f"- **State:** `{state}`")
    st.markdown(f"- **Metric:** `{metric_name_map[health_metric]}`")

    health_df_filtered = filter_by_state(health_df, state)

    if health_df_filtered.empty:
        st.warning(f"No health data available for {state if state != 'All' else 'the selected states'}.")
    else:
        # Income histogram
        st.markdown(f"**Low-Income Distribution Across Counties in {state if state != 'All' else 'All States'}**")
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

        # Top counties by health metric
        health_df_filtered = health_df_filtered.copy()
        health_df_filtered[health_metric] = pd.to_numeric(health_df_filtered[health_metric], errors='coerce')
        top = health_df_filtered.sort_values(by=health_metric, ascending=False).head(top_n)
        top = top.dropna(subset=[health_metric])

        st.markdown(f"### Top {top_n} Counties by {metric_name_map[health_metric]} in {state if state != 'All' else 'All States'}")

        if top.empty:
            st.warning(f"No data available for {metric_name_map[health_metric]}.")
        else:
            bar = px.bar(
                top,
                x="County",
                y=health_metric,
                color="State",
                title=f"Top {top_n} Counties for {metric_name_map[health_metric]}",
                hover_data=["MEAN_low_income_percentage"],
                color_discrete_sequence=["#2D584A"],
                template="plotly_white"
            )
            bar.update_layout(font=dict(family="Arial", size=12))
            bar.update_yaxes(title_text=metric_name_map[health_metric])
            bar.update_traces(hovertemplate="County: %{x}<br>" + metric_name_map[health_metric] + ": %{y}<br>" + metric_name_map["MEAN_low_income_percentage"] + ": %{customdata}")
            st.plotly_chart(bar, use_container_width=True)

            # Data table
            display_df = top[["County", "State", health_metric, "MEAN_low_income_percentage"]].copy()
            display_df.columns = ["County", "State", metric_name_map[health_metric], metric_name_map["MEAN_low_income_percentage"]]
            table_html = "<table style='border-collapse: collapse; width: 100%;'>"
            table_html += "<thead><tr>"
            for col in display_df.columns:
                table_html += f"<th style='font-family: Arial; border: 1px solid black; padding: 5px;'>{col}</th>"
            table_html += "</tr></thead><tbody>"
            for i in range(len(display_df)):
                table_html += "<tr>"
                for col in display_df.columns:
                    val = display_df.iloc[i][col]
                    if isinstance(val, float):
                        val = f"{val:.1f}"
                    table_html += f"<td style='font-family: Arial; border: 1px solid black; padding: 5px;'>{val}</td>"
                table_html += "</tr>"
            table_html += "</tbody></table>"
            st.markdown(table_html, unsafe_allow_html=True)

# --- Key Findings (footer) ---
st.markdown("---")
st.markdown("### Key Findings")

# Compute findings
if not health_df.empty:
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
    else:
        asthma_finding = "Insufficient data to identify top asthma counties across states."
else:
    asthma_finding = "No health data available."

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
    else:
        wildfire_finding = "Insufficient data to identify high wildfire risk counties."
else:
    wildfire_finding = "No wildfire data available with risk >= 50."

st.markdown(f"**Health and Income Disparities:** {asthma_finding}")
st.markdown(f"**Wildfire Risk Patterns:** {wildfire_finding}")
