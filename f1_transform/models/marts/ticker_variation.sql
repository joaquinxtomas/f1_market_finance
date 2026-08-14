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
INNER JOIN stg_ticker_data b
ON rr.constructor = b.constructor
AND rr.race_date > b.ticker_date AND b.ticker_date >= rr.race_date - INTERVAL 3 DAYS
INNER JOIN stg_ticker_data a
ON rr.constructor = a.constructor
AND rr.race_date < a.ticker_date AND a.ticker_date <= rr.race_date + INTERVAL 3 DAYS
AND b.ticker = a.ticker
GROUP BY rr.constructor,rr.round, rr.race_name, rr.race_date, b.ticker, b.ticker_close, a.ticker_close
ORDER BY rr.round