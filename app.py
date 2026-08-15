import streamlit as st
import duckdb
import plotly.express as px

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

fig = px.bar(data, x="race_date", y="before_close", color="ticker", title=f"Evolución de sponsors - {carrera}")
st.plotly_chart(fig)