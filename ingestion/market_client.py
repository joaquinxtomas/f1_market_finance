import yfinance as yf
import pandas as pd

df = pd.read_csv("../data/seeds/sponsors_publicly_traded.csv")

def get_info_ticker(df, constructor, start_date, end_date) -> dict:
    df = df[df["constructor"] == constructor]

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
        except Exception as e:
            print(f"[ERROR] Fallo al consultad {t}: {e}")
    return info

l = get_info_ticker(df, "Ferrari", "2026-7-24","2026-7-28")
print(l)