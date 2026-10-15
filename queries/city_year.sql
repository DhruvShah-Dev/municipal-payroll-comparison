SELECT city, year, basis,
       CAST(overtime_pay_usd AS REAL) / CAST(total_pay_usd AS REAL) AS overtime_share,
       CAST(overtime_pay_usd AS REAL) / 1000000000.0 AS overtime_pay_billion_usd,
       CAST(total_pay_usd AS REAL) / 1000000000.0 AS total_pay_billion_usd
FROM city_year_summary
ORDER BY city, year;
