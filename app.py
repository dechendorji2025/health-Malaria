import streamlit as st
import pandas as pd
import plotly.express as px

# Load the data
@st.cache_data
def load_data():
    df = pd.read_csv("data/malaria_indicators_btn.csv")
    return df

df = load_data()

st.title("Bhutan Malaria Indicators Dashboard")
st.write("""
Bhutan has made significant progress toward eliminating malaria, achieving zero indigenous (locally acquired) cases nationwide since 2021. The remaining risk is restricted to imported cases from neighboring India, primarily in the southern districts.This is a simple dashboard I made for learning purposes. 
Below are the main things included in this Streamlit app:

- Load processed healthcare data
- Show different trend charts over the years
- A small model prediction widget (coming soon)
- A dashboard for key malaria indicators
- District-wise map for Bhutan (basic version for now)

I will keep improving this as I learn more.
""")
st.write("This simple dashboard shows malaria-related indicators over the years.")

# Rename columns for easier use
df = df.rename(columns={
    "GHO (DISPLAY)": "indicator_name",
    "YEAR (DISPLAY)": "year",
    "Numeric": "value_num"
})

# convert numeric column properly
df["value_num"] = pd.to_numeric(df["value_num"], errors="coerce")

# Sidebar – only select indicator
indicator_list = df["indicator_name"].dropna().unique()

selected_indicator = st.sidebar.selectbox(
    "Select an Indicator",
    indicator_list
)

# Filter data
filtered_df = df[df["indicator_name"] == selected_indicator]

st.subheader(f"Indicator: {selected_indicator}")

# Bar chart
st.write("### Bar Chart")
fig_bar = px.bar(
    filtered_df,
    x="year",
    y="value_num",
    title=f"{selected_indicator} Over Years"
)
st.plotly_chart(fig_bar, use_container_width=True)

# Line chart
st.write("### Line Chart")
fig_line = px.line(
    filtered_df,
    x="year",
    y="value_num",
    markers=True
)
st.plotly_chart(fig_line, use_container_width=True)

# Show data table
st.write("### Data Table")
st.dataframe(filtered_df)

st.header("Bhutan District Map")

import pydeck as pdk
import json
import pandas as pd

geojson = json.load(open("data/bhutan_districts.json"))
st.header("Malaria Case Summary and Map")

# --- Overall maximum across Bhutan ---
max_cases = df["value_num"].max()
max_year = df.loc[df["value_num"].idxmax(), "year"]
st.write(f"**Maximum malaria cases in Bhutan:** {max_cases} (Year: {max_year})")

# --- District-level analysis ---
if "District" in df.columns:
    # Compute max, min, and average per district
    district_stats = df.groupby("District")["value_num"].agg(
        max_cases="max",
        min_cases="min",
        avg_cases="mean"
    ).reset_index()

    # Identify top and bottom districts
    top_district = district_stats.loc[district_stats["max_cases"].idxmax()]
    min_district = district_stats.loc[district_stats["min_cases"].idxmin()]

    st.write(f"**District with highest malaria cases:** {top_district['District']} ({top_district['max_cases']} cases)")
    st.write(f"**District with minimum malaria cases:** {min_district['District']} ({min_district['min_cases']} cases)")

    # --- Merge stats into GeoJSON ---
    for feature in geojson["features"]:
        district_name = feature["properties"]["DISTRICT"]  # adjust key if needed
        match = district_stats[district_stats["District"] == district_name]
        if not match.empty:
            feature["properties"]["max_cases"] = int(match["max_cases"])
            feature["properties"]["min_cases"] = int(match["min_cases"])
            feature["properties"]["avg_cases"] = float(match["avg_cases"])
        else:
            feature["properties"]["max_cases"] = 0
            feature["properties"]["min_cases"] = 0
            feature["properties"]["avg_cases"] = 0

    # --- Assign colors: red (max), green (min), yellow (average) ---
    layer = pdk.Layer(
        "GeoJsonLayer",
        geojson,
        stroked=True,
        filled=True,
        get_fill_color="""
            [properties.max_cases == properties.max_cases ? [255, 0, 0, 150] :
             properties.min_cases == properties.min_cases ? [0, 200, 0, 150] :
             [255, 255, 0, 150]]
        """,
        pickable=True,
    )

    view_state = pdk.ViewState(
        latitude=27.5,
        longitude=90.4,
        zoom=7
    )

    st.pydeck_chart(
        pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            tooltip={"text": "{DISTRICT}\\nMax: {max_cases}\\nMin: {min_cases}\\nAvg: {avg_cases}"}
        )
    )
else:
    st.warning("No district column found in dataset. Please add district info to plot cases.")
