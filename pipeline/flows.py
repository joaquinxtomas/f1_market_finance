import duckdb
import pandas as pd
from prefect import flow
from ingestion import f1_client, market_client

@flow
def actualizar_pipeline():
    con = duckdb.connect("../data/f1_market.duckdb")
    ultimo_round_cargado = con.sql("SELECT MAX(race_round) FROM raw_race_results").fetchone()[0]
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
        
        rows_tickers
