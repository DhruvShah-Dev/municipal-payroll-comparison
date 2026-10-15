SELECT city, 'Regular pay' AS component,
       CAST(regular_pay_usd AS REAL) / CAST(total_pay_usd AS REAL) AS share,
       CAST(regular_pay_usd AS REAL) / 1000000000.0 AS amount_billion_usd
FROM city_year_summary WHERE year = '2025'
UNION ALL
SELECT city, 'Overtime',
       CAST(overtime_pay_usd AS REAL) / CAST(total_pay_usd AS REAL),
       CAST(overtime_pay_usd AS REAL) / 1000000000.0
FROM city_year_summary WHERE year = '2025'
UNION ALL
SELECT city, 'Other pay',
       CAST(other_pay_usd AS REAL) / CAST(total_pay_usd AS REAL),
       CAST(other_pay_usd AS REAL) / 1000000000.0
FROM city_year_summary WHERE year = '2025'
ORDER BY city, component;
