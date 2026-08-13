import yfinance as yf
import pandas as pd

df = pd.read_csv("data/seeds/sponsors_publicly_traded.csv")

def get_info_ticker(df, constructor, race_date) -> tuple:

    info = {}
    errores=[]

    df = df[df["constructor"] == constructor]

    race_dt = pd.Timestamp(race_date)

    start_date = (race_dt - pd.offsets.BusinessDay(n=1)).strftime("%Y-%m-%d")
    end_date = (race_dt + pd.offsets.BusinessDay(n=2)).strftime("%Y-%m-%d")

    ticker_list = df["yfinance_ticker"].tolist()
    info={}
    for t in ticker_list:
        try:
            ticker = yf.Ticker(t)
            historial = ticker.history(start=start_date, end=end_date)
            if not historial.empty:
                info[t] = historial
            else:
                print(f"[WARNING] Sin datos para {t} entre {start_date} y {end_date}")
                errores.append({"ticker": t, "constructor": constructor, "start_date": start_date, "end_date": end_date})
        except Exception as e:
            print(f"[ERROR] Fallo al consultar {t}: {e}")
            errores.append({"ticker": t, "constructor": constructor, "start_date": start_date, "end_date": end_date})

    return info, errores