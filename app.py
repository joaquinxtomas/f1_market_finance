import streamlit as st
import duckdb
import plotly.graph_objects as go
import pandas as pd

CONSTRUCTOR_MAP = {
    "ferrari": "Ferrari",
    "mercedes": "Mercedes",
    "red_bull": "Red Bull",
    "mclaren": "McLaren",
    "aston_martin": "Aston Martin",
    "alpine": "Alpine",
    "williams": "Williams",
    "haas": "Haas",
    "rb": "Racing Bulls",
    "audi": "Audi",
    "cadillac": "Cadillac"
}

con = duckdb.connect("data/f1_market.duckdb")
st.title("Variación porcentual de empresas patrocinadoras en la Fórmula 1")

constructors = con.sql("SELECT DISTINCT constructor FROM ticker_variation ORDER BY constructor").fetchdf()
escuderia = st.selectbox("Seleccioná una escudería", constructors["constructor"], format_func=lambda x: CONSTRUCTOR_MAP.get(x,x), key="escuderia")

races = con.sql(f"SELECT DISTINCT race_name FROM ticker_variation WHERE constructor = '{escuderia}' ORDER BY round").fetchdf()
carrera = st.selectbox("Seleccioná una carrera", races["race_name"], key="carrera")

race_date = con.sql(f"""
    SELECT DISTINCT race_date 
    FROM ticker_variation 
    WHERE constructor = '{escuderia}' AND race_name = '{carrera}'
""").fetchone()[0]

tickers = con.sql(f"SELECT DISTINCT ticker FROM ticker_variation WHERE constructor = '{escuderia}'").fetchdf()
ticker_seleccionado = st.selectbox("Seleccioná un ticker", tickers["ticker"], key="ticker")

historial = con.sql(f"""
    SELECT ticker_date, ticker_open, high, low, ticker_close, volume
    FROM stg_ticker_data
    WHERE ticker = '{ticker_seleccionado}'
    AND constructor = '{escuderia}'
    AND race_date = '{race_date}'
    ORDER BY ticker_date
""").fetchdf()

historial["ticker_date"] = pd.to_datetime(historial["ticker_date"])

tipo_grafico = st.radio("Tipo de gráfico", ["Líneas", "Velas"], key="tipo_grafico")

if tipo_grafico == "Velas":

    fig = go.Figure(data=[go.Candlestick(
        x=historial["ticker_date"],
        open=historial["ticker_open"],
        high=historial["high"],
        low=historial["low"],
        close=historial["ticker_close"]
    )])
else:
    fig = go.Figure(data =[go.Scatter(
        x=historial["ticker_date"],
        y=historial["ticker_close"],
        mode="lines"
    )])

fig.add_vline(
    x=pd.to_datetime(race_date),
    line_dash="dash",
    line_color="yellow",
    annotation_text=f"Race Day",
    annotation_position="top left"
)

fig.update_xaxes(
    range=[historial["ticker_date"].min(), historial["ticker_date"].max()],
    dtick=86400000,
    tickformat="%b %d"
)

metricas = con.sql(f"""
    SELECT before_close, after_close, variacion_porcentual, maxima_posicion
    FROM ticker_variation
    WHERE constructor = '{escuderia}'
    AND race_name = '{carrera}'
    AND ticker = '{ticker_seleccionado}'
""").fetchone()

col1, col2, col3 = st.columns(3)
col1.metric("Close before", f"{metricas[0]:.2f}")
col2.metric("Close after", f"{metricas[1]:.2f}", f"{metricas[2]:.2f}%")
col3.metric("Mejor posición", int(metricas[3]))

st.plotly_chart(fig)