import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

# ------------------------
# Data Source
# ------------------------
URL_DATA = "https://storage.dosm.gov.my/gdp/gdp_annual_nominal_supply.parquet"

@st.cache_data
def load_data():
    df = pd.read_parquet(URL_DATA)

    # Date & year
    df['date'] = pd.to_datetime(df['date'])
    df['year'] = df['date'].dt.year

    # Ensure numeric GDP values
    df['value'] = pd.to_numeric(df['value'], errors='coerce')

    # Sector mapping
    sector_map = {
        'p1': 'Agriculture',
        'p2': 'Mining',
        'p3': 'Manufacturing',
        'p4': 'Construction',
        'p5': 'Services',
        'p6': 'Import Duties'
    }

    # Map sectors, others treated as Total GDP
    df['sector'] = df['sector'].map(sector_map).fillna('Total GDP')

    return df.dropna(subset=['year', 'value'])

# Load data
df = load_data()

# ------------------------
# App Title
# ------------------------
st.title("📊 Malaysia Nominal GDP Analysis Dashboard")

# ------------------------
# Sidebar Selection
# ------------------------
graph_option = st.sidebar.selectbox(
    "Select analysis to view:",
    [
        "Total GDP Trend",
        "Sector Contribution",
        "YoY Growth by Sector",
        "Sector Volatility",
        "Sector Correlation",
        "Total GDP Forecast"
    ]
)

# ========================
# 1. Total GDP Trend
# ========================
if graph_option == "Total GDP Trend":
    st.header("Total Nominal GDP Trend")

    total = df.groupby('year')['value'].sum().reset_index()

    chart = (
        alt.Chart(total)
        .mark_line(point=True)
        .encode(
            x=alt.X('year:O', title='Year'),
            y=alt.Y('value:Q', title='GDP Value'),
            tooltip=['year', 'value']
        )
    )

    st.altair_chart(chart, use_container_width=True)

# ========================
# 2. Sector Contribution
# ========================
elif graph_option == "Sector Contribution":
    st.header("Sector Contribution to GDP")

    sector_data = df[df['sector'] != 'Total GDP']
    sector_data = sector_data.groupby(['year', 'sector'])['value'].sum().reset_index()

    chart = (
        alt.Chart(sector_data)
        .mark_bar()
        .encode(
            x=alt.X('year:O', title='Year'),
            y=alt.Y('value:Q', title='GDP Value'),
            color='sector:N',
            tooltip=['sector', 'value']
        )
    )

    st.altair_chart(chart, use_container_width=True)

# ========================
# 3. YoY Growth
# ========================
elif graph_option == "YoY Growth by Sector":
    st.header("Year-on-Year Growth by Sector (%)")

    yoy = (
        df[df['sector'] != 'Total GDP']
        .groupby(['sector', 'year'])['value']
        .sum()
        .reset_index()
    )

    yoy['yoy_growth'] = yoy.groupby('sector')['value'].pct_change() * 100
    yoy = yoy.dropna()

    chart = (
        alt.Chart(yoy)
        .mark_line(point=True)
        .encode(
            x=alt.X('year:O', title='Year'),
            y=alt.Y('yoy_growth:Q', title='Growth Rate (%)'),
            color='sector:N',
            tooltip=['sector', 'yoy_growth']
        )
    )

    st.altair_chart(chart, use_container_width=True)

# ========================
# 4. Sector Volatility
# ========================
elif graph_option == "Sector Volatility":
    st.header("Sector Volatility (Standard Deviation of YoY Growth)")

    yoy = (
        df[df['sector'] != 'Total GDP']
        .groupby(['sector', 'year'])['value']
        .sum()
        .reset_index()
    )

    yoy['yoy_growth'] = yoy.groupby('sector')['value'].pct_change() * 100

    volatility = (
        yoy.groupby('sector')['yoy_growth']
        .std()
        .reset_index()
        .sort_values(by='yoy_growth', ascending=False)
    )

    chart = (
        alt.Chart(volatility)
        .mark_bar()
        .encode(
            x=alt.X('yoy_growth:Q', title='Volatility'),
            y=alt.Y('sector:N', sort='-x'),
            tooltip=['sector', 'yoy_growth']
        )
    )

    st.altair_chart(chart, use_container_width=True)

# ========================
# 5. Sector Correlation
# ========================
elif graph_option == "Sector Correlation":
    st.header("Sector GDP Correlation Matrix")

    df_corr = df[df['sector'] != 'Total GDP']

    pivot = (
        df_corr.groupby(['year', 'sector'])['value']
        .sum()
        .reset_index()
        .pivot(index='year', columns='sector', values='value')
    )

    corr = pivot.corr().reset_index().melt(
        id_vars='sector',
        var_name='sector_2',
        value_name='correlation'
    )

    chart = (
        alt.Chart(corr)
        .mark_rect()
        .encode(
            x='sector:O',
            y='sector_2:O',
            color=alt.Color(
                'correlation:Q',
                scale=alt.Scale(scheme='redblue'),
                legend=alt.Legend(title='Correlation')
            ),
            tooltip=['sector', 'sector_2', 'correlation']
        )
    )

    st.altair_chart(chart, use_container_width=True)

# ========================
# 6. GDP Forecast
# ========================
elif graph_option == "Total GDP Forecast":
    st.header("Total GDP Forecast")

    years_ahead = st.slider("Forecast Years Ahead", 1, 10, 5)

    total = df.groupby('year')['value'].sum().reset_index()

    X = total['year'].values
    y = total['value'].values

    # Log-linear regression
    log_y = np.log(y)
    coef = np.polyfit(X, log_y, 1)
    trend = np.poly1d(coef)

    future_years = np.arange(X.max() + 1, X.max() + years_ahead + 1)
    forecast_values = np.exp(trend(future_years))

    forecast_df = pd.DataFrame({
        'year': np.concatenate([X, future_years]),
        'value': np.concatenate([y, forecast_values]),
        'type': ['Historical'] * len(X) + ['Forecast'] * len(future_years)
    })

    chart = (
        alt.Chart(forecast_df)
        .mark_line(point=True)
        .encode(
            x=alt.X('year:O', title='Year'),
            y=alt.Y('value:Q', title='GDP Value'),
            color='type:N',
            tooltip=['year', 'value']
        )
    )

    st.altair_chart(chart, use_container_width=True)
