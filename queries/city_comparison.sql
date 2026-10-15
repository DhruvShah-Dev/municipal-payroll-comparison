SELECT curr.city, curr.basis,
       CAST(curr.total_pay_usd AS REAL) / 1000000000.0 AS total_pay_billion_usd,
       CAST(curr.overtime_pay_usd AS REAL) / 1000000000.0 AS overtime_pay_billion_usd,
       CAST(curr.overtime_pay_usd AS REAL) / CAST(curr.total_pay_usd AS REAL) AS overtime_share,
       100.0 * (CAST(curr.overtime_pay_usd AS REAL) / CAST(curr.total_pay_usd AS REAL)
                - CAST(prev.overtime_pay_usd AS REAL) / CAST(prev.total_pay_usd AS REAL)) AS share_change_pp,
       CAST(curr.overtime_pay_usd AS REAL) / CAST(prev.overtime_pay_usd AS REAL) - 1.0 AS overtime_dollar_change
FROM city_year_summary AS curr
JOIN city_year_summary AS prev ON prev.city = curr.city AND prev.year = '2024'
WHERE curr.year = '2025'
ORDER BY curr.city;
