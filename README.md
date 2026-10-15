# Three-city payroll comparison

This portfolio project compares **municipal government payroll spending** in New York City, Chicago, and San Francisco using official open data. It does **not** describe everyone employed in the wider metropolitan areas.

Open the [summary report](report.html), then use its **Next page: comparison** link to reach the [detailed comparison](comparison.html). The pages are snapshots of source data retrieved **October 15, 2026**.

## Sources

| City | Official dataset | Grain used here | 2025 window |
| --- | --- | --- | --- |
| New York City | [Citywide Payroll Data (Fiscal Year)](https://data.cityofnewyork.us/City-Government/Citywide-Payroll-Data-Fiscal-Year-/k397-673e) | Employee fiscal-year record | Fiscal year ending June 30, 2025 |
| Chicago | [Employee Payroll Data (FMPS Payroll Costing)](https://data.cityofchicago.org/Administration-Finance/Employee-Payroll-Data-FMPS-Payroll-Costing-/dawh-m56b) | Employee pay element in payroll period | Payroll year 2025, periods 1–24 |
| San Francisco | [Employee Compensation](https://data.sf.gov/d/88g8-5mnd) | Employee/job/department/year-type record | Fiscal year ending June 30, 2025 |

San Francisco publishes overlapping fiscal and calendar views; this project filters to **Fiscal** only. Its [dataset FAQ](https://sfdigitalservices.gitbook.io/dataset-explainers/employee-compensation-faq) says an employee may have multiple rows in a year. Chicago warns that its extract is unaudited and payroll periods do not necessarily match earnings periods. Counts of source records are therefore **not** comparable employee headcounts.

## Key measure

`Overtime share = overtime pay / (regular pay + overtime pay + other pay)`.

NYC and San Francisco publish overtime as a field. Chicago publishes pay elements, so [analyze.py](analyze.py) maps elements whose names begin with `OT` or include `OVERTIME` or `QUARTERLY OT` into an **analyst-defined overtime proxy**. Chicago's denominator is the sum of *all* published pay elements. San Francisco benefits are excluded from salary pay. These choices make the comparison useful for exploring payroll structure, but not for ranking labor efficiency or pay practices.

## Findings

| City | 2025 overtime pay | 2025 reported pay | Overtime share | 2024 overtime share |
| --- | ---: | ---: | ---: | ---: |
| New York City | $2.922B | $34.596B | 8.45% | 8.57% |
| Chicago | $0.470B | $4.394B | 10.69% | 12.39% |
| San Francisco | $0.471B | $5.258B | 8.96% | 9.53% |

Within the published 2025 data, police and fire departments together account for about 57% of NYC overtime, 73% of Chicago overtime, and 46% of San Francisco overtime. These are shares of each city's own overtime spend; department responsibilities and coverage differ.

Chicago's $161.1M `PR YR RETRO PEN` element raises its 2025 total-pay denominator. Excluding that single element for a sensitivity check raises Chicago's 2025 overtime share from 10.69% to about **11.10%**; it remains below the 2024 value. This does not reclassify all retroactive pay or make the cities fully comparable.

## Reproduce

Run from the repository root (Python 3.11+; standard library only):

```powershell
python analyze.py
python build_report.py
python build_comparison.py
python validate_snapshot.py
```

`analyze.py` calls the three Socrata APIs and writes reviewed aggregate outputs to [data](data). It checks that pay components reconcile, Chicago has all 24 payroll periods in both comparison years, and department subtotals reconcile to city totals. The two build scripts use SQLite and the saved [SQL queries](queries) to create [summary](artifact.json) and [comparison](comparison_artifact.json) artifacts. Both HTML pages were packaged from those artifacts with the Data Analytics portable builder. [patch_portable_html.py](patch_portable_html.py) adds local page navigation and corrects the builder's top bar width when a vertical scrollbar appears. Both packaged pages passed desktop and mobile browser verification.

The HTML files are ready to open. Regenerating the HTML from the JSON artifacts requires the Data Analytics portable builder available in this environment; the Python steps above reproduce the data and report inputs without that builder.

GitHub Actions runs `validate_snapshot.py` on each push and pull request. It checks city-year coverage, arithmetic, department subtotals, Chicago period coverage, and links between the two report pages without depending on live API availability.

The project intentionally saves **aggregate results only**; it does not download employee names or individual pay records. Public sources may be revised, so rerunning the scripts can change the numbers.

## Next analysis

Study which departments drove year-over-year overtime changes within each city, then join comparable staffing or worked-hours data before making efficiency claims. For Chicago, seek an official pay-element category map before treating its overtime proxy as final.
