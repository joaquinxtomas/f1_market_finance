SELECT 
    CAST(r.season AS INTEGER) as season,
    CAST(r.round AS INTEGER) as round,
    r.race_name as race_name,
    CAST(r.date AS date) as race_date,
    r.driver as driver, 
    r.constructor as constructor,
    CAST(r.position AS INTEGER) as position
FROM raw_race_results r