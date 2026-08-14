WITH t_before AS (
    SELECT 
        ticker,
        constructor,
        MIN(ticker_date) AS before_date,
        ticker_open as before_open,
        ticker_close as before_close,
        high as before_high,
        low as before_low,
        volume as before_volume
    FROM stg_ticker_data
    GROUP BY ticker, constructor, ticker_open, ticker_close, high, low, volume
),
t_after AS(
    SELECT 
        ticker,
        constructor,
        MAX(ticker_date) AS after_date,
        ticker_open as after_open,
        ticker_close as after_close,
        high as after_high,
        low as after_low,
        volume as after_volume
    FROM stg_ticker_data
    GROUP BY ticker, constructor, ticker_open, ticker_close, high, low, volume
)
SELECT 
    rr.race_round,
    rr.race_name,
    rr.race_date,
    MAX(rr.position),
    b.ticker,
    b.before_close,
    a.after_close
FROM stg_race_results rr
INNER JOIN t_before b
ON rr.constructor = b.constructor
AND rr.date < b.before_date
INNER JOIN t_after a
ON rr.constructor = a.constructor
AND rr.date > a.after_date
