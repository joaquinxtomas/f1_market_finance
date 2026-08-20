import streamlit as st
import duckdb
import plotly.graph_objects as go
import plotly.express as px
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
st.title("F1 Sponsor Stock Variation")

constructors = con.sql("SELECT DISTINCT constructor FROM ticker_variation ORDER BY constructor").fetchdf()
escuderia = st.selectbox("Select a constructor", constructors["constructor"], format_func=lambda x: CONSTRUCTOR_MAP.get(x,x), key="escuderia")

tab1, tab2 = st.tabs(["Race Analysis", "Season Overview"])

with tab1:
    races = con.sql(f"SELECT DISTINCT race_name FROM ticker_variation WHERE constructor = '{escuderia}' ORDER BY round").fetchdf()
    carrera = st.selectbox("Select a race", races["race_name"], key="carrera")

    race_date = con.sql(f"""
        SELECT DISTINCT race_date 
        FROM ticker_variation 
        WHERE constructor = '{escuderia}' AND race_name = '{carrera}'
    """).fetchone()[0]

    tickers = con.sql(f"SELECT DISTINCT ticker FROM ticker_variation WHERE constructor = '{escuderia}'").fetchdf()
    ticker_seleccionado = st.selectbox("Select a ticker", tickers["ticker"], key="ticker")

    historial = con.sql(f"""
        SELECT ticker_date, ticker_open, high, low, ticker_close, volume
        FROM stg_ticker_data
        WHERE ticker = '{ticker_seleccionado}'
        AND constructor = '{escuderia}'
        AND race_date = '{race_date}'
        ORDER BY ticker_date
    """).fetchdf()

    currency = con.sql(f"""
        SELECT DISTINCT currency
        FROM stg_ticker_data
        WHERE ticker = '{ticker_seleccionado}'
    """).fetchone()[0]

    historial["ticker_date"] = pd.to_datetime(historial["ticker_date"])

    tipo_grafico = st.radio("Chart type", ["Lines", "Candlestick"], key="tipo_grafico", horizontal=True)

    if tipo_grafico == "Candlestick":

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
        SELECT before_close, after_close, price_change_pct, best_position
        FROM ticker_variation
        WHERE constructor = '{escuderia}'
        AND race_name = '{carrera}'
        AND ticker = '{ticker_seleccionado}'
    """).fetchone()

    col1, col2, col3 = st.columns(3)
    col1.metric("Close before", f"{currency} {metricas[0]:.2f}")
    col2.metric("Close after", f"{currency} {metricas[1]:.2f}", f"{metricas[2]:.2f}%")
    col3.metric("Best position", int(metricas[3]))

    st.plotly_chart(fig, use_container_width=True)

    tabla = con.sql(f"""
        SELECT ticker, before_close, after_close, price_change_pct
        FROM ticker_variation
        WHERE constructor = '{escuderia}' AND race_name = '{carrera}'
        ORDER BY price_change_pct DESC
    """).fetchdf()

    st.subheader(f"All sponsors - {CONSTRUCTOR_MAP.get(escuderia, escuderia)} in {carrera}")
    st.dataframe(
        tabla.style.map(
            lambda v: 'color:green' if v > 0 else 'color:red',
            subset=['price_change_pct']
        ),
        use_container_width=True
    )

    promedio = con.sql(f"""
        SELECT constructor, AVG(price_change_pct) as avg_variation
        FROM ticker_variation
        WHERE race_name = '{carrera}'
        GROUP BY constructor
        ORDER BY avg_variation DESC
    """).fetchdf()

    fig_promedio = px.bar(
        promedio,
        x="constructor",
        y="avg_variation",
        color="avg_variation",
        color_continuous_scale=["red","gray","green"],
        color_continuous_midpoint=0
    )
    st.subheader(f"Average variation per constructor - {carrera}")
    st.plotly_chart(fig_promedio, use_container_width=True)


with tab2:
    promedio = con.sql(f"""
        SELECT constructor, AVG(price_change_pct) as avg_variation
        FROM ticker_variation
        GROUP BY constructor
        ORDER BY avg_variation DESC
    """).fetchdf()
    fig_promedio_general = px.bar(
        promedio,
        x="constructor",
        y="avg_variation",
        color="avg_variation",
        color_continuous_scale=["red","gray","green"],
        color_continuous_midpoint=0
    )
    st.subheader(f"Average sponsor variation per constructor - 2026 Season")
    st.plotly_chart(fig_promedio_general, use_container_width=True)

