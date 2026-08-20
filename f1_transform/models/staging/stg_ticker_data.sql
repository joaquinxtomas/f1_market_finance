SELECT 
    td.ticker AS ticker,
    td.constructor AS constructor,
    CAST(race_date AS DATE) AS race_date,
    CAST(td.date AS DATE) AS ticker_date,
    td.currency as currency,
    td.open AS ticker_open,
    td.close AS ticker_close,
    td.high AS high,
    td.low AS low, 
    td.volume AS volume
FROM raw_ticker_data td