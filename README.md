# F1 Sponsor Stock Variation Pipeline

An end-to-end data engineering pipeline that explores whether Formula 1 race results have any measurable impact on the stock prices of team sponsors.

**[Live Dashboard](https://f1-stock-analysis.streamlit.app/)**

## The Question

Every F1 team is backed by publicly traded sponsors — from tech giants like Google (McLaren) and Microsoft (Mercedes) to consumer brands like Coca-Cola (McLaren) and Heineken (Red Bull). Do their stock prices move differently around race weekends depending on how their sponsored team performs?

This project builds the infrastructure to investigate that question: ingesting race results and stock market data, transforming them into a unified analytical model, and presenting the findings through an interactive dashboard.

## Architecture

```
[Jolpica F1 API]     [Yahoo Finance]     [Curated CSV]
       │                    │                   │
       └────── httpx ───────┘──── yfinance ─────┘
                            │
                     Python (pandas)
                            │
                      ┌─────▼─────┐
                      │  DuckDB   │
                      │  (raw)    │
                      └─────┬─────┘
                            │
                        dbt-core
                            │
                      ┌─────▼─────┐
                      │  DuckDB   │
                      │  (marts)  │
                      └─────┬─────┘
                            │
                        Streamlit
                            │
                      ┌─────▼─────┐
                      │ Dashboard │
                      └───────────┘

        Orchestrated with Prefect
```

## Stack

| Layer | Tool | Purpose |
|---|---|---|
| Ingestion | httpx, yfinance | F1 race data and stock prices |
| Storage | DuckDB | Lightweight analytical database |
| Transformation | dbt-core | SQL-based data modeling (staging → marts) |
| Orchestration | Prefect | Pipeline scheduling, retries, monitoring |
| Visualization | Streamlit + Plotly | Interactive dashboard |
| Environment | uv | Fast dependency management |

## Data Sources

**Jolpica F1 API** — Race results, calendar, constructor and driver data. Open source successor to the Ergast API.

**Yahoo Finance (via yfinance)** — Daily OHLCV stock data for sponsor tickers across 10 exchanges worldwide (NYSE, NASDAQ, Frankfurt, Euronext, Tokyo, London, and others).

**Curated sponsor seed file** — A manually researched CSV mapping each F1 constructor to its publicly traded sponsors, including ticker symbols, exchanges, yfinance-compatible tickers, and trading currencies. Covers all 11 teams with 100+ sponsors across 10 currencies (USD, EUR, JPY, GBP, SEK, CHF, SAR, KRW, HKD, CAD).

## Data Model

### Raw Layer
- `raw_race_results` — One row per driver per race (season, round, race name, date, driver, constructor, position)
- `raw_ticker_data` — Daily OHLCV data per ticker per race weekend (ticker, constructor, race date, price date, currency, OHLCV)

### Staging Layer (dbt)
- `stg_race_results` — Cleaned types: integers for season/round/position, proper date casting
- `stg_ticker_data` — Normalized dates, consistent column naming

### Mart Layer (dbt)
- `ticker_variation` — One row per ticker per race: close before, close after, price change percentage, and the constructor's best finishing position. Uses `ROW_NUMBER()` window functions to select exactly the last trading day before and first trading day after each race.

## Pipeline Modes

The Prefect flow supports two execution modes:

**Incremental** (`full_reload=False`) — Detects the last loaded race round, fetches only new races and their corresponding stock data, and appends to existing tables.

**Full reload** (`full_reload=True`) — Drops all tables and reingests the entire season from scratch. Used when the data schema changes or a complete refresh is needed.

## Dashboard

The Streamlit dashboard provides two views:

**Race Analysis** — Select a constructor, race, and ticker to see:
- Candlestick or line chart of stock prices around the race weekend
- Pre/post race close prices and percentage variation with currency
- Summary table of all sponsor variations for that constructor in that race
- Average variation per constructor for the selected race

**Season Overview** — Average sponsor stock variation per constructor across all races in the 2026 season.

## Setup

### Prerequisites
- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager

### Installation

```bash
git clone https://github.com/joaquinxtomas/f1_market_finance.git
cd f1_market_finance
uv sync
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

### Configure dbt

Create `~/.dbt/profiles.yml`:

```yaml
f1_transform:
  outputs:
    dev:
      type: duckdb
      path: /absolute/path/to/f1_market_finance/data/f1_market.duckdb
      threads: 1
  target: dev
```

### Run the pipeline

```bash
# Full load (first time)
python -m pipeline.flows

# Run dbt transformations
cd f1_transform && dbt run && cd ..

# Launch dashboard
streamlit run app.py
```

## Project Structure

```
f1_market_finance/
├── ingestion/
│   ├── f1_client.py          # Jolpica F1 API client
│   └── market_client.py      # Yahoo Finance client
├── pipeline/
│   └── flows.py              # Prefect orchestration flow
├── storage/
│   └── loader.py             # Initial data loader (development)
├── f1_transform/             # dbt project
│   └── models/
│       ├── staging/
│       │   ├── stg_race_results.sql
│       │   └── stg_ticker_data.sql
│       └── marts/
│           └── ticker_variation.sql
├── data/
│   ├── f1_market.duckdb      # DuckDB database
│   └── seeds/
│       └── sponsors_publicly_traded.csv
├── notebooks/                # Exploration and ad-hoc queries
├── app.py                    # Streamlit dashboard
└── pyproject.toml
```

## Key Decisions

**DuckDB over PostgreSQL** — No server setup, single-file database, excellent pandas integration. Ideal for a portfolio project that anyone can clone and run.

**Prefect over Airflow** — Lighter footprint, Python-native flow definitions, no infrastructure overhead. Concepts (tasks, flows, retries, scheduling) transfer directly to Airflow.

**Curated sponsor data** — No API provides F1 sponsor information. The seed file was manually researched and represents a common real-world data engineering pattern: not everything comes from an API.

**Window functions for price selection** — After expanding the data window from 1 to 5 business days around each race, the mart needed `ROW_NUMBER()` to select exactly the last close before and first close after each race, avoiding duplicate rows from multiple trading days within the window.

## Limitations

- Stock price movements around race weekends are influenced by many factors beyond F1 results (earnings, macroeconomics, sector trends). This project measures correlation, not causation.
- Sponsor data was curated for the 2026 season. Sponsor relationships change between seasons.
- Some tickers were delisted between seasons (Smartsheet, Alteryx, Ansys, MoneyGram) and are excluded.
- Stock prices are in native exchange currencies. Percentage variation is currency-independent, but absolute prices are not comparable across sponsors.