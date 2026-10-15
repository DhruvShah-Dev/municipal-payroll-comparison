WITH ranked AS (
  SELECT d.city, d.department,
         CAST(d.overtime_pay_usd AS REAL) / 1000000.0 AS overtime_million_usd,
         CAST(d.overtime_pay_usd AS REAL) / CAST(s.overtime_pay_usd AS REAL) AS share_of_city_overtime,
         CAST(d.overtime_pay_usd AS REAL) / CAST(d.total_pay_usd AS REAL) AS share_of_department_pay,
         ROW_NUMBER() OVER (PARTITION BY d.city ORDER BY CAST(d.overtime_pay_usd AS REAL) DESC) AS rank
  FROM department_2025 AS d
  JOIN city_year_summary AS s ON s.city = d.city AND s.year = '2025'
  WHERE CAST(d.total_pay_usd AS REAL) > 0
)
SELECT city, rank, department, overtime_million_usd,
       share_of_city_overtime, share_of_department_pay
FROM ranked
WHERE rank <= 5
ORDER BY city, rank;
