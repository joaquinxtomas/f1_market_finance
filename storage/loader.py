import duckdb
from ingestion import f1_client, market_client
import json
import pandas as pd
import time

calendario = f1_client.get_data_api(2026, "races")

for carrera in calendario:
    if(carrera["date"] <= pd.Timestamp.now().strftime("%Y-%m-%d")):
        max_race = carrera["round"]
        max_race = int(max_race)

rows_races=[]
for i in range(1,max_race + 1):
    json_txt = f1_client.get_data_api(2026, "results", i)
    for carrera in json_txt:
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
df_sponsors = pd.read_csv("data/seeds/sponsors_publicly_traded.csv")

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

rows_tickers=[]
for i, fila in pares.iterrows():
    r = market_client.get_info_ticker(df_sponsors, CONSTRUCTOR_MAP[fila["constructor"]], fila["date"])
    time.sleep(2)
    for ticker, historial in r.items():
        for fecha, fila_precio in historial.iterrows():
            row = {
                "ticker": ticker,
                "constructor":fila["constructor"],
                "date":fecha,
                "open": fila_precio["Open"],
                "close": fila_precio["Close"],
                "high": fila_precio["High"],
                "low": fila_precio["Low"],
                "volume": fila_precio["Volume"]
            }
            rows_tickers.append(row)

df_tickers=pd.DataFrame(rows_tickers)

print(df_tickers)

#with duckdb.connect("data/f1_market.duckdb") as con:
#    con.sql("CREATE OR REPLACE TABLE raw_race_results AS SELECT * FROM df_races")
#    con.sql("SELECT * FROM raw_race_results").show()