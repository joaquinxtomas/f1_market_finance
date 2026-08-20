import duckdb
import pandas as pd
import time
import subprocess
from prefect import flow
from ingestion import f1_client, market_client

@flow
def actualizar_pipeline(full_reload=False):
    con = duckdb.connect("data/f1_market.duckdb")

    if full_reload:
        con.sql("DROP TABLE IF EXISTS raw_race_results")
        con.sql("DROP TABLE IF EXISTS raw_ticker_data")
        ultimo_round_cargado=0
        print(f"Full reload activado. Ultimo round: {ultimo_round_cargado}")
    else:
        ultimo_round_cargado = con.sql("SELECT MAX(CAST(round AS INTEGER)) FROM raw_race_results").fetchone()[0]
        if ultimo_round_cargado is None:
            ultimo_round_cargado = 0

    carreras = f1_client.get_data_api(2026, "races")
    
    for carrera in carreras:
        if(carrera["date"] <= pd.Timestamp.now().strftime("%Y-%m-%d")):
            max_race =  int(carrera["round"])
    
    rows_races=[]
    if(max_race > ultimo_round_cargado):
        for i in range(ultimo_round_cargado + 1, max_race + 1):
            resultados = f1_client.get_data_api(2026, "results", i)
            for carrera in resultados:
                for resultado in carrera["Results"]:
                    row = {
                        "season": carrera["season"],
                        "round": carrera["round"],
                        "race_name": carrera["raceName"],
                        "date": carrera["date"],
                        "driver": resultado["Driver"]["driverId"],
                        "constructor": resultado["Constructor"]["constructorId"],
                        "position": resultado["position"]
                    }
                    rows_races.append(row)
        df_races = pd.DataFrame(rows_races)
        
        pares = df_races[["date", "constructor"]].drop_duplicates()
        
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
        
        rows_tickers = []

        df_sponsors = pd.read_csv("data/seeds/sponsors_publicly_traded.csv")

        for i, fila in pares.iterrows():
            r, _ = market_client.get_info_ticker(df_sponsors, CONSTRUCTOR_MAP[fila["constructor"]], fila["date"])
            time.sleep(2)
            for ticker, historial in r.items():
                currency = df_sponsors[df_sponsors["yfinance_ticker"] == ticker]["currency"].values[0]
                for fecha, fila_precio in historial.iterrows():
                    row = {
                        "ticker": ticker,
                        "constructor": fila["constructor"],
                        "race_date": fila["date"],
                        "date": fecha,
                        "currency": currency,
                        "open": fila_precio["Open"],
                        "close": fila_precio["Close"],
                        "high": fila_precio["High"],
                        "low": fila_precio["Low"],
                        "volume": fila_precio["Volume"]
                    }
                    rows_tickers.append(row)
        df_tickers = pd.DataFrame(rows_tickers)

        if full_reload:
            con.sql("CREATE OR REPLACE TABLE raw_race_results AS SELECT * FROM df_races")
            con.sql("CREATE OR REPLACE TABLE raw_ticker_data AS SELECT * FROM df_tickers")
        else:
            con.sql("INSERT INTO raw_race_results SELECT * FROM df_races")
            con.sql("INSERT INTO raw_race_results SELECT * FROM df_tickers")
            
        con.close()
        subprocess.run(["dbt", "run"], cwd="f1_transform", check=True)
    else:
        print("No hay carreras nuevas.")


if __name__ == "__main__":
    actualizar_pipeline(full_reload=True)