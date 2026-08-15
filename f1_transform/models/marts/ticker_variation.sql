WITH before_ranked AS (
    SELECT
    ticker, constructor, race_date, ticker_date, ticker_close,
    ROW_NUMBER() OVER(PARTITION BY ticker, constructor, race_date ORDER BY ticker_date DESC) AS rn
    FROM stg_ticker_data
    WHERE ticker_date < race_date
),
after_ranked AS (
    SELECT
    ticker, constructor, race_date, ticker_date, ticker_close,
    ROW_NUMBER() OVER(PARTITION BY ticker, constructor, race_date ORDER BY ticker_date ASC) AS rn
    FROM stg_ticker_data
    WHERE ticker_date > race_date
)
SELECT 
    rr.constructor,
    rr.round,
    rr.race_name,
    rr.race_date,
    MIN(rr.position) as maxima_posicion,
    b.ticker,
    b.ticker_close as before_close,
    a.ticker_close as after_close,
    ((a.ticker_close - b.ticker_close) / b.ticker_close) * 100 as variacion_porcentual
FROM stg_race_results rr
INNER JOIN before_ranked b
ON rr.constructor = b.constructor
AND rr.race_date = b.race_date 
AND b.rn = 1
INNER JOIN after_ranked a
ON rr.constructor = a.constructor
AND rr.race_date = a.race_date AND a.rn = 1
AND b.ticker = a.ticker
GROUP BY rr.constructor,rr.round, rr.race_name, rr.race_date, b.ticker, b.ticker_close, a.ticker_close
ORDER BY rr.round