import streamlit as st
import duckdb
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
import pandas as pd

con = duckdb.connect("data/f1_market.duckdb")
st.title("Variacion porcentual de empresas patrocinadoras en la formula 1")
constructors = con.sql("SELECT DISTINCT constructor FROM ticker_variation ORDER BY constructor").fetchdf()
escuderia = st.selectbox("Selecciona una escuderia", constructors["constructor"])
races = con.sql(f"SELECT DISTINCT race_name FROM ticker_variation WHERE constructor = '{escuderia}' ORDER BY round").fetchdf()
carrera = st.selectbox("Selecciona una carrera", races["race_name"])

data = con.sql(f"""
    SELECT race_date, ticker, before_close, after_close, variacion_porcentual 
    FROM ticker_variation
    WHERE constructor = '{escuderia}' AND race_name = '{carrera}' 
""").fetchdf()

tickers = con.sql(f"SELECT DISTINCT ticker FROM ticker_variation WHERE constructor = '{escuderia}'").fetchdf()
ticker_seleccionado = st.selectbox("Selecciona un ticker", tickers["ticker"])

ticker = yf.Ticker(ticker_seleccionado)
historial = con.sql(f"""
                        SELECT ticker_data, ticker_open, high, low, ticker_close, volume
                        FROM stg_ticker_data
                        WHERE ticker = '{ticker_seleccionado}'
                        AND constructor = '{escuderia}'
                    """).fetchdf()
fig = go.Figure(data = [go.Candlestick(
    x=historial.index,
    open=historial["Open"],
    high = historial["High"],
    low=historial["Low"],
    close=historial["Close"]
)])
st.plotly_chart(fig)