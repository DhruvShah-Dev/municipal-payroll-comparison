SELECT m.city, m.service, m.department,
       CAST(d.overtime_pay_usd AS REAL) / 1000000000.0 AS overtime_pay_billion_usd,
       CAST(d.overtime_pay_usd AS REAL) / CAST(s.overtime_pay_usd AS REAL) AS share_of_city_overtime
FROM service_map AS m
JOIN department_2025 AS d ON d.city = m.city AND d.department = m.department
JOIN city_year_summary AS s ON s.city = m.city AND s.year = '2025'
ORDER BY m.city, m.service;
