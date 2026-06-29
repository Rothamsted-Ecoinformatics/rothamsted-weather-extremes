import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Rothamsted Temperature Extremes",
    layout="wide"
)

st.title("Rothamsted Temperature Extremes")

@st.cache_data
def load_data():
    data = pd.read_csv("all_temps.csv")

    # Convert columns
    data["day"] = pd.to_datetime(data["day"], format="%d-%m-%Y", errors="coerce")
    data["tmin"] = pd.to_numeric(data["tmin"], errors="coerce")
    data["tmax"] = pd.to_numeric(data["tmax"], errors="coerce")

    # Remove rows with no date
    data = data.dropna(subset=["day"])

    return data


# Load data
with st.spinner("Loading data..."):
    data = load_data()

row_count = len(data)

st.success(f"Loading data... done, {row_count:,} records loaded!")

with st.form("query_form"):

    col1, col2 = st.columns(2)

    with col1:
        temperature = st.number_input(
            "Enter a temperature threshold (°C)",
            value=30.0,
            step=0.1,
            format="%.1f"
        )

    with col2:
        temp_type = st.radio(
            "Temperature type",
            ["tmin", "tmax"],
            horizontal=True
        )

    submitted = st.form_submit_button("Run query")

# Filter data
filtered = data.dropna(subset=[temp_type])
filtered = filtered[filtered[temp_type] >= temperature]

st.write(f"Temperature threshold: **{temperature:.1f} °C**")
st.write(f"Temperature variable: **{temp_type}**")
st.write(f"Matching records: **{len(filtered):,}**")


if filtered.empty:
    st.warning("No records match the selected criteria.")

else:
    # Aggregate by year
    annual = (
        filtered
        .assign(year=filtered["day"].dt.year)
        .groupby("year")
        .agg(
            mean_t=(temp_type, "mean"),
            min_t=(temp_type, "min"),
            max_t=(temp_type, "max"),
            n_observations=(temp_type, "size")
        )
        .reset_index()
    )

    annual["mean_t"] = annual["mean_t"].round(2)
    annual["min_t"] = annual["min_t"].round(2)
    annual["max_t"] = annual["max_t"].round(2)

    # Create Plotly bubble plot
    fig = px.scatter(
        annual,
        x="year",
        y="mean_t",
        size="n_observations",
        color="mean_t",
        color_continuous_scale="Reds",
        hover_data={
            "year": True,
            "mean_t": ":.2f",
            "min_t": ":.2f",
            "max_t": ":.2f",
            "n_observations": True
        },
        labels={
            "year": "Year",
            "mean_t": f"Mean {temp_type} temperature (°C)",
            "min_t": f"Minimum {temp_type} temperature (°C)",
            "max_t": f"Maximum {temp_type} temperature (°C)",
            "n_observations": "Number of observations"
        },
        title=(
            f"Annual {temp_type} events ≥ {temperature:.1f}°C "
            "for Rothamsted Research, Harpenden, UK"
        )
    )

    fig.update_traces(
        marker=dict(
            line=dict(
                width=1,
                color="black"
            ),
            opacity=0.75
        )
    )

    fig.update_layout(
        height=600,
        xaxis_title="Year",
        yaxis_title=f"Mean {temp_type} temperature (°C)",
        coloraxis_colorbar_title="Mean temperature (°C)",
        template="plotly_white"
    )

    st.plotly_chart(fig, use_container_width=True)

    with st.expander("Show annual summary data"):
        st.dataframe(annual, use_container_width=True)

    with st.expander("Show matching daily records"):
        st.dataframe(filtered, use_container_width=True)