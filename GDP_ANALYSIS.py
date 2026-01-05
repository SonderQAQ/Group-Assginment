import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

# ------------------------
# 数据源
# ------------------------
URL_DATA = "https://storage.dosm.gov.my/gdp/gdp_annual_nominal_supply.parquet"

@st.cache_data
def load_data():
    df = pd.read_parquet(URL_DATA)
    df['date'] = pd.to_datetime(df['date'])
    df['year'] = df['date'].dt.year
    df['value'] = pd.to_numeric(df['value'], errors='coerce')
    if 'sector' not in df.columns:
        df['sector'] = 'Total'
    return df.dropna(subset=['year','value'])

df = load_data()

st.title("📊 Malaysia GDP Dashboard")

# ------------------------
# Sidebar - 选择 graph
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
            x='year:O',
            y='value:Q',
            tooltip=['year', 'value']
        )
    )
    st.altair_chart(chart, use_container_width=True)

# ========================
# 2. Sector Contribution
# ========================
elif graph_option == "Sector Contribution":
    st.header("Sector Contribution Over Years")
    sector_data = df[df['sector'] != 'p0']  # 删除 Total GDP
    sector_data = sector_data.groupby(['year','sector'])['value'].sum().reset_index()
    chart = (
        alt.Chart(sector_data)
        .mark_bar()
        .encode(
            x='year:O',
            y='value:Q',
            color='sector:N',
            tooltip=['sector','value']
        )
    )
    st.altair_chart(chart, use_container_width=True)

# ========================
# 3. YoY Growth
# ========================
elif graph_option == "YoY Growth by Sector":
    st.header("Year-on-Year Growth by Sector")
    yoy = df[df['sector'] != 'p0'].groupby(['sector','year'])['value'].sum().reset_index()
    yoy['yoy_pct'] = yoy.groupby('sector')['value'].pct_change() * 100
    yoy = yoy.dropna()
    chart = (
        alt.Chart(yoy)
        .mark_line(point=True)
        .encode(
            x='year:O',
            y='yoy_pct:Q',
            color='sector:N',
            tooltip=['sector','yoy_pct']
        )
    )
    st.altair_chart(chart, use_container_width=True)

# ========================
# 4. Volatility
# ========================
elif graph_option == "Sector Volatility":
    st.header("Sector Volatility (Std Dev of YoY %)")
    yoy = df[df['sector'] != 'p0'].groupby(['sector','year'])['value'].sum().reset_index()
    yoy['yoy_pct'] = yoy.groupby('sector')['value'].pct_change() * 100
    vol = yoy.groupby('sector')['yoy_pct'].std().reset_index().sort_values(by='yoy_pct', ascending=False).head(10)
    chart = (
        alt.Chart(vol)
        .mark_bar()
        .encode(
            x='yoy_pct:Q',
            y=alt.Y('sector:N', sort='-x'),
            tooltip=['sector','yoy_pct']
        )
    )
    st.altair_chart(chart, use_container_width=True)

# ========================
# 5. Correlation
# ========================
elif graph_option == "Sector Correlation":
    st.header("Sector GDP Correlation (Excluding Total GDP)")
    df_corr = df[df['sector'] != 'p0']
    pivot = df_corr.groupby(['year','sector'])['value'].sum().reset_index().pivot(index='year', columns='sector', values='value')
    corr = pivot.corr().reset_index().melt(id_vars='sector', var_name='sector_2', value_name='corr')
    chart = (
        alt.Chart(corr)
        .mark_rect()
        .encode(
            x='sector:O',
            y='sector_2:O',
            color=alt.Color('corr:Q', scale=alt.Scale(scheme='redblue'), legend=alt.Legend(title="Correlation")),
            tooltip=['sector','sector_2','corr']
        )
    )
    st.altair_chart(chart, use_container_width=True)

# ========================
# 6. Forecast
# ========================
elif graph_option == "Total GDP Forecast":
    st.header("Total GDP Forecast")
    years_ahead = st.slider("Years Ahead", 1, 10, 5)
    total = df.groupby('year')['value'].sum().reset_index()
    X = total['year'].values
    y = total['value'].values
    mask = y > 0
    X, y = X[mask], y[mask]
    log_y = np.log(y)
    coef = np.polyfit(X, log_y, 1)
    trend = np.poly1d(coef)
    future_years = np.arange(X.max()+1, X.max()+years_ahead+1)
    forecast_values = np.exp(trend(future_years))
    forecast_df = pd.DataFrame({
        'year': np.concatenate([X,future_years]),
        'value': np.concatenate([y,forecast_values]),
        'type': ['Historical']*len(X)+['Forecast']*len(future_years)
    })
    chart = (
        alt.Chart(forecast_df)
        .mark_line(point=True)
        .encode(
            x='year:O',
            y='value:Q',
            color='type:N',
            tooltip=['year','value']
        )
    )
    st.altair_chart(chart, use_container_width=True)
