import duckdb
import pandas as pd
import time
import subprocess
from prefect import flow
from ingestion import f1_client, market_client

@flow
def actualizar_pipeline():
    con = duckdb.connect("data/f1_market.duckdb")
    ultimo_round_cargado = con.sql("SELECT MAX(CAST(round AS INTEGER)) FROM raw_race_results").fetchone()[0]
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
        con.sql("INSERT INTO raw_race_results SELECT * FROM df_races")
        
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
                for fecha, fila_precio in historial.iterrows():
                    row = {
                        "ticker": ticker,
                        "constructor": fila["constructor"],
                        "date": fecha,
                        "open": fila_precio["Open"],
                        "close": fila_precio["Close"],
                        "high": fila_precio["High"],
                        "low": fila_precio["Low"],
                        "volume": fila_precio["Volume"]
                    }
                    rows_tickers.append(row)
        df_tickers = pd.DataFrame(rows_tickers)

        con.sql("INSERT INTO raw_ticker_data SELECT * FROM df_tickers")

        subprocess.run(["dbt", "run"], cwd="f1_transform", check=True)
    else:
        print("No hay carreras nuevas.")

    con.close()

if __name__ == "__main__":
    actualizar_pipeline()