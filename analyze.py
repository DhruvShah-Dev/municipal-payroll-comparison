"""Reproduce a public, aggregate comparison of municipal payroll spending.

Run: python metro-payroll-comparison/analyze.py
Requires only the Python standard library and access to the three Socrata APIs.
"""

from __future__ import annotations

import csv
import json
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "data"
OUT.mkdir(exist_ok=True)
BASES = {
    "New York City": "https://data.cityofnewyork.us/resource/k397-673e.json",
    "Chicago": "https://data.cityofchicago.org/resource/dawh-m56b.json",
    "San Francisco": "https://data.sf.gov/resource/88g8-5mnd.json",
}
YEAR = 2025


def fetch(city: str, **params: str) -> list[dict]:
    url = BASES[city] + "?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, headers={"User-Agent": "MetroPayrollPortfolio/1.0"})
    with urllib.request.urlopen(request, timeout=180) as response:
        return json.load(response)


def money(row: dict, key: str) -> Decimal:
    return Decimal(row.get(key) or "0")


def csv_write(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise ValueError(f"No rows for {path.name}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def overtime_element(element: str) -> bool:
    # Conservative, inspectable proxy. Chicago does not publish a canonical OT flag.
    return bool(re.search(r"(^OT\b|\bOVERTIME\b|\bQUARTERLY OT\b)", element))


def main() -> None:
    nyc = fetch(
        "New York City",
        **{
            "$select": "fiscal_year,count(*) as rows,sum(regular_gross_paid) as regular,sum(total_ot_paid) as overtime,sum(total_other_pay) as other",
            "$where": "fiscal_year in(2024,2025)",
            "$group": "fiscal_year",
            "$order": "fiscal_year",
        },
    )
    sf = fetch(
        "San Francisco",
        **{
            "$select": "year,count(*) as rows,sum(salaries) as regular,sum(overtime) as overtime,sum(other_salaries) as other,sum(total_salary) as total_salary,sum(total_benefits) as benefits",
            "$where": "year_type='Fiscal' and year in('2024','2025')",
            "$group": "year",
            "$order": "year",
        },
    )
    chicago = fetch(
        "Chicago",
        **{
            "$select": "payroll_year,pay_element,count(*) as rows,sum(amount) as amount",
            "$where": "payroll_year in(2024,2025)",
            "$group": "payroll_year,pay_element",
            "$order": "payroll_year,pay_element",
            "$limit": "1000",
        },
    )
    periods = fetch(
        "Chicago",
        **{
            "$select": "payroll_year,min(payroll_period) as first_period,max(payroll_period) as last_period,count(distinct payroll_period) as periods,count(*) as rows",
            "$where": "payroll_year in(2024,2025)",
            "$group": "payroll_year",
            "$order": "payroll_year",
        },
    )
    nyc_departments = fetch(
        "New York City",
        **{
            "$select": "agency_name,sum(regular_gross_paid) as regular,sum(total_ot_paid) as overtime,sum(total_other_pay) as other",
            "$where": "fiscal_year=2025",
            "$group": "agency_name",
            "$limit": "1000",
        },
    )
    sf_departments = fetch(
        "San Francisco",
        **{
            "$select": "department,sum(salaries) as regular,sum(overtime) as overtime,sum(other_salaries) as other",
            "$where": "year_type='Fiscal' and year='2025'",
            "$group": "department",
            "$limit": "1000",
        },
    )
    chicago_departments = fetch(
        "Chicago",
        **{
            "$select": "department,pay_element,sum(amount) as amount",
            "$where": "payroll_year=2025",
            "$group": "department,pay_element",
            "$limit": "10000",
        },
    )
    raw = {"nyc": nyc, "sf": sf, "chicago_pay_elements": chicago, "chicago_periods": periods,
           "nyc_departments": nyc_departments, "sf_departments": sf_departments,
           "chicago_departments": chicago_departments}
    (OUT / "source_aggregates.json").write_text(json.dumps(raw, indent=2), encoding="utf-8")

    summary = []
    for row in nyc:
        regular, ot, other = (money(row, x) for x in ("regular", "overtime", "other"))
        total = regular + ot + other
        summary.append({
            "city": "New York City", "year": row["fiscal_year"], "basis": "Fiscal year (July-June)",
            "records": row["rows"], "regular_pay_usd": f"{regular:.2f}", "overtime_pay_usd": f"{ot:.2f}",
            "other_pay_usd": f"{other:.2f}", "total_pay_usd": f"{total:.2f}",
            "overtime_share_pct": f"{100 * ot / total:.4f}", "classification": "published field",
        })
    for row in sf:
        regular, ot, other = (money(row, x) for x in ("regular", "overtime", "other"))
        total = money(row, "total_salary")
        if abs(total - regular - ot - other) > Decimal("0.01"):
            raise ValueError("SF total_salary does not reconcile")
        summary.append({
            "city": "San Francisco", "year": row["year"], "basis": "Fiscal year (July-June)",
            "records": row["rows"], "regular_pay_usd": f"{regular:.2f}", "overtime_pay_usd": f"{ot:.2f}",
            "other_pay_usd": f"{other:.2f}", "total_pay_usd": f"{total:.2f}",
            "overtime_share_pct": f"{100 * ot / total:.4f}", "classification": "published field",
        })
    for year in (2024, 2025):
        entries = [r for r in chicago if int(r["payroll_year"]) == year]
        regular = sum((money(r, "amount") for r in entries if r["pay_element"] in ("REGULAR SALARY", "REGULAR TIME")), Decimal())
        ot = sum((money(r, "amount") for r in entries if overtime_element(r["pay_element"])), Decimal())
        total = sum((money(r, "amount") for r in entries), Decimal())
        other = total - regular - ot
        summary.append({
            "city": "Chicago", "year": str(year), "basis": "Payroll year (24 periods)",
            "records": str(sum(int(r["rows"]) for r in entries)), "regular_pay_usd": f"{regular:.2f}",
            "overtime_pay_usd": f"{ot:.2f}", "other_pay_usd": f"{other:.2f}",
            "total_pay_usd": f"{total:.2f}", "overtime_share_pct": f"{100 * ot / total:.4f}",
            "classification": "analyst-coded pay elements",
        })
    summary.sort(key=lambda r: (r["city"], r["year"]))
    csv_write(OUT / "city_year_summary.csv", summary)

    departments = []
    for city, rows, label in (("New York City", nyc_departments, "agency_name"),
                              ("San Francisco", sf_departments, "department")):
        for row in rows:
            regular, ot, other = (money(row, x) for x in ("regular", "overtime", "other"))
            departments.append({"city": city, "department": row[label],
                                "total_pay_usd": f"{regular + ot + other:.2f}",
                                "overtime_pay_usd": f"{ot:.2f}"})
    by_department = {}
    for row in chicago_departments:
        dept = row["department"]
        sums = by_department.setdefault(dept, {"total": Decimal(), "ot": Decimal()})
        amount = money(row, "amount")
        sums["total"] += amount
        if overtime_element(row["pay_element"]):
            sums["ot"] += amount
    for dept, sums in by_department.items():
        departments.append({"city": "Chicago", "department": dept,
                            "total_pay_usd": f"{sums['total']:.2f}",
                            "overtime_pay_usd": f"{sums['ot']:.2f}"})
    departments.sort(key=lambda r: (r["city"], -Decimal(r["overtime_pay_usd"])))
    csv_write(OUT / "department_2025.csv", departments)

    # Sanity checks, retained with the delivered snapshot.
    for row in summary:
        total = Decimal(row["total_pay_usd"])
        components = sum((Decimal(row[key]) for key in ("regular_pay_usd", "overtime_pay_usd", "other_pay_usd")), Decimal())
        assert abs(total - components) <= Decimal("0.01"), row
        assert total > 0 and Decimal(row["overtime_pay_usd"]) >= 0, row
    assert len(summary) == 6
    assert all(int(r["periods"]) == 24 and int(r["first_period"]) == 1 and int(r["last_period"]) == 24 for r in periods)
    for city in BASES:
        department_rows = [r for r in departments if r["city"] == city]
        city_row = next(r for r in summary if r["city"] == city and r["year"] == "2025")
        for key in ("total_pay_usd", "overtime_pay_usd"):
            assert abs(sum((Decimal(r[key]) for r in department_rows), Decimal())
                       - Decimal(city_row[key])) <= Decimal("0.10"), (city, key)
    metadata = {"retrieved_utc": datetime.now(timezone.utc).isoformat(), "year": YEAR, "sources": BASES, "checks": "Six city-year rows; components reconcile; Chicago has periods 1-24 in both years."}
    (OUT / "run_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(json.dumps({"summary": summary, "chicago_periods": periods, "metadata": metadata}, indent=2))


if __name__ == "__main__":
    main()
