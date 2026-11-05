"""Build the aggregate snapshot used by the municipal payroll data story.

Only grouped totals are requested; employee-level rows are never downloaded.
Run from the repository root with ``python analyze.py``.
"""

from __future__ import annotations

import csv
import json
import math
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "data"
OUT.mkdir(exist_ok=True)
BASES = {
    "New York City": "https://data.cityofnewyork.us/resource/k397-673e.json",
    "Chicago": "https://data.cityofchicago.org/resource/dawh-m56b.json",
    "San Francisco": "https://data.sf.gov/resource/88g8-5mnd.json",
}
SOURCE_PAGES = {
    "New York City": "https://data.cityofnewyork.us/City-Government/Citywide-Payroll-Data-Fiscal-Year-/k397-673e",
    "Chicago": "https://data.cityofchicago.org/Administration-Finance/Employee-Payroll-Data-FMPS-Payroll-Costing-/dawh-m56b",
    "San Francisco": "https://data.sfgov.org/City-Management-and-Ethics/Employee-Compensation/88g8-5mnd",
}
CHICAGO_COMPLETE_PERIODS = 24
STORY_YEAR_COUNT = 3


def fetch(city: str, **params: str) -> list[dict]:
    """Fetch one aggregate Socrata query with bounded retries."""
    url = BASES[city] + "?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, headers={"User-Agent": "MunicipalPayrollStory/2.0"})
    last_error: Exception | None = None
    for attempt in range(4):
        try:
            with urllib.request.urlopen(request, timeout=240) as response:
                payload = json.load(response)
            if isinstance(payload, dict) and payload.get("error"):
                raise RuntimeError(payload.get("message", "Socrata query failed"))
            return payload
        except (urllib.error.URLError, TimeoutError, RuntimeError) as exc:
            last_error = exc
            if attempt < 3:
                time.sleep(2**attempt)
    raise RuntimeError(f"Unable to retrieve aggregate data for {city}: {last_error}")


def money(row: dict, key: str) -> Decimal:
    return Decimal(str(row.get(key) or "0"))


def as_float(value: Decimal) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"Non-finite numeric result: {value}")
    return result


def csv_write(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise ValueError(f"No rows for {path.name}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def overtime_element(element: str) -> bool:
    """Conservative Chicago proxy retained from the original project."""
    return bool(re.search(r"(^OT\b|\bOVERTIME\b|\bQUARTERLY OT\b)", element.upper()))


def year_list(years: Iterable[int | str]) -> str:
    return ",".join(str(int(year)) for year in years)


def quoted_year_list(years: Iterable[int]) -> str:
    return ",".join(f"'{year}'" for year in years)


def discover_story_years() -> tuple[list[int], list[dict]]:
    nyc_years = {int(row["fiscal_year"]) for row in fetch(
        "New York City", **{"$select": "fiscal_year,count(*) as rows", "$group": "fiscal_year", "$order": "fiscal_year", "$limit": "100"}
    )}
    sf_years = {int(row["year"]) for row in fetch(
        "San Francisco", **{"$select": "year,count(*) as rows", "$where": "year_type='Fiscal'", "$group": "year", "$order": "year", "$limit": "100"}
    )}
    chicago_periods = fetch("Chicago", **{
        "$select": "payroll_year,min(payroll_period) as first_period,max(payroll_period) as last_period,count(distinct payroll_period) as periods,count(*) as rows",
        "$group": "payroll_year", "$order": "payroll_year", "$limit": "100",
    })
    chicago_complete = {
        int(row["payroll_year"]) for row in chicago_periods
        if int(row["periods"]) == CHICAGO_COMPLETE_PERIODS
        and int(row["first_period"]) == 1 and int(row["last_period"]) == CHICAGO_COMPLETE_PERIODS
    }
    common = sorted(nyc_years & sf_years & chicago_complete)
    if len(common) < STORY_YEAR_COUNT:
        raise ValueError(f"Need {STORY_YEAR_COUNT} common complete years; found {common}")
    return common[-STORY_YEAR_COUNT:], chicago_periods


def city_year_row(city: str, year: int, basis: str, records: int | str, regular: Decimal, overtime: Decimal, other: Decimal, classification: str) -> dict:
    total = regular + overtime + other
    if total <= 0:
        raise ValueError(f"Non-positive city total for {city} {year}")
    return {
        "city": city, "year": year, "basis": basis, "source_records": int(records),
        "regular_pay_usd": as_float(regular), "overtime_pay_usd": as_float(overtime),
        "other_pay_usd": as_float(other), "total_pay_usd": as_float(total),
        "overtime_share": as_float(overtime / total), "classification": classification,
    }


def build_city_years(years: list[int]) -> tuple[list[dict], list[dict]]:
    years_sql = year_list(years)
    nyc = fetch("New York City", **{
        "$select": "fiscal_year,count(*) as rows,sum(regular_gross_paid) as regular,sum(total_ot_paid) as overtime,sum(total_other_pay) as other",
        "$where": f"fiscal_year in({years_sql})", "$group": "fiscal_year", "$order": "fiscal_year", "$limit": "100",
    })
    sf = fetch("San Francisco", **{
        "$select": "year,count(*) as rows,sum(salaries) as regular,sum(overtime) as overtime,sum(other_salaries) as other,sum(total_salary) as total_salary,sum(total_benefits) as benefits",
        "$where": f"year_type='Fiscal' and year in({quoted_year_list(years)})", "$group": "year", "$order": "year", "$limit": "100",
    })
    chicago = fetch("Chicago", **{
        "$select": "payroll_year,pay_element,count(*) as rows,sum(amount) as amount",
        "$where": f"payroll_year in({years_sql})", "$group": "payroll_year,pay_element", "$order": "payroll_year,pay_element", "$limit": "10000",
    })
    result: list[dict] = []
    for row in nyc:
        regular, overtime, other = (money(row, field) for field in ("regular", "overtime", "other"))
        result.append(city_year_row("New York City", int(row["fiscal_year"]), "Fiscal year (July–June)", row["rows"], regular, overtime, other, "published field"))
    for row in sf:
        regular, overtime, other = (money(row, field) for field in ("regular", "overtime", "other"))
        if abs(money(row, "total_salary") - regular - overtime - other) > Decimal("0.01"):
            raise ValueError(f"San Francisco total salary does not reconcile for {row['year']}")
        result.append(city_year_row("San Francisco", int(row["year"]), "Fiscal year (July–June)", row["rows"], regular, overtime, other, "published field"))
    for year in years:
        entries = [row for row in chicago if int(row["payroll_year"]) == year]
        regular = sum((money(row, "amount") for row in entries if row["pay_element"] in {"REGULAR SALARY", "REGULAR TIME"}), Decimal())
        overtime = sum((money(row, "amount") for row in entries if overtime_element(row["pay_element"])), Decimal())
        total = sum((money(row, "amount") for row in entries), Decimal())
        result.append(city_year_row("Chicago", year, "Payroll year (24 periods)", sum(int(row["rows"]) for row in entries), regular, overtime, total - regular - overtime, "analyst-classified pay elements"))
    result.sort(key=lambda row: (row["city"], row["year"]))
    previous_by_city: dict[str, dict] = {}
    for row in result:
        previous = previous_by_city.get(row["city"])
        row["overtime_change_usd"] = None if previous is None else row["overtime_pay_usd"] - previous["overtime_pay_usd"]
        row["overtime_share_change_pp"] = None if previous is None else (row["overtime_share"] - previous["overtime_share"]) * 100
        previous_by_city[row["city"]] = row
    return result, chicago


def department_row(city: str, year: int, department: str, total: Decimal, overtime: Decimal) -> dict:
    return {"city": city, "year": year, "department": department.strip(), "total_pay_usd": as_float(total), "overtime_pay_usd": as_float(overtime)}


def build_departments(years: list[int], city_years: list[dict]) -> list[dict]:
    years_sql = year_list(years)
    nyc = fetch("New York City", **{
        "$select": "fiscal_year,agency_name,sum(regular_gross_paid) as regular,sum(total_ot_paid) as overtime,sum(total_other_pay) as other",
        "$where": f"fiscal_year in({years_sql})", "$group": "fiscal_year,agency_name", "$limit": "10000",
    })
    sf = fetch("San Francisco", **{
        "$select": "year,department,sum(salaries) as regular,sum(overtime) as overtime,sum(other_salaries) as other",
        "$where": f"year_type='Fiscal' and year in({quoted_year_list(years)})", "$group": "year,department", "$limit": "10000",
    })
    chicago = fetch("Chicago", **{
        "$select": "payroll_year,department,pay_element,sum(amount) as amount",
        "$where": f"payroll_year in({years_sql})", "$group": "payroll_year,department,pay_element", "$limit": "50000",
    })
    rows: list[dict] = []
    for city, source_rows, year_key, department_key in (("New York City", nyc, "fiscal_year", "agency_name"), ("San Francisco", sf, "year", "department")):
        for row in source_rows:
            regular, overtime, other = (money(row, field) for field in ("regular", "overtime", "other"))
            rows.append(department_row(city, int(row[year_key]), row[department_key], regular + overtime + other, overtime))
    chicago_groups: dict[tuple[int, str], dict[str, Decimal]] = defaultdict(lambda: {"total": Decimal(), "overtime": Decimal()})
    for row in chicago:
        key = (int(row["payroll_year"]), row["department"])
        amount = money(row, "amount")
        chicago_groups[key]["total"] += amount
        if overtime_element(row["pay_element"]):
            chicago_groups[key]["overtime"] += amount
    for (year, department), totals in chicago_groups.items():
        rows.append(department_row("Chicago", year, department, totals["total"], totals["overtime"]))
    city_lookup = {(row["city"], row["year"]): row for row in city_years}
    by_department: dict[tuple[str, str], dict[int, dict]] = defaultdict(dict)
    for row in rows:
        city = city_lookup[(row["city"], row["year"])]
        row["share_of_city_overtime"] = row["overtime_pay_usd"] / city["overtime_pay_usd"]
        row["overtime_share_of_department_pay"] = 0 if row["total_pay_usd"] == 0 else row["overtime_pay_usd"] / row["total_pay_usd"]
        by_department[(row["city"], row["department"])][row["year"]] = row
    for history in by_department.values():
        previous: dict | None = None
        for year in years:
            current = history.get(year)
            if current is not None:
                current["overtime_change_usd"] = None if previous is None else current["overtime_pay_usd"] - previous["overtime_pay_usd"]
                previous = current
    rows.sort(key=lambda row: (row["city"], row["year"], -row["overtime_pay_usd"], row["department"]))
    return rows


def build_story_data(years: list[int], city_years: list[dict], departments: list[dict], chicago_elements: list[dict], chicago_periods: list[dict], retrieved_at: str) -> dict:
    latest, prior = years[-1], years[-2]
    latest_departments = [row for row in departments if row["year"] == latest]
    top_departments: list[dict] = []
    concentrations: list[dict] = []
    drivers: list[dict] = []
    for city in sorted(BASES):
        ranked = sorted((row for row in latest_departments if row["city"] == city), key=lambda row: row["overtime_pay_usd"], reverse=True)
        top = ranked[:5]
        top_departments.extend({**row, "rank": rank} for rank, row in enumerate(top, 1))
        concentrations.append({"city": city, "year": latest, "top_five_share": sum(row["share_of_city_overtime"] for row in top)})
        changes = [row for row in ranked if row["overtime_change_usd"] is not None]
        chosen = sorted(changes, key=lambda row: abs(row["overtime_change_usd"]), reverse=True)[:7]
        city_delta = next(row["overtime_change_usd"] for row in city_years if row["city"] == city and row["year"] == latest)
        for row in chosen:
            drivers.append({key: row[key] for key in ("city", "year", "department", "overtime_change_usd", "overtime_pay_usd", "share_of_city_overtime", "overtime_share_of_department_pay")})
        remaining = [row for row in changes if row not in chosen]
        drivers.append({
            "city": city, "year": latest, "department": "All other departments",
            "overtime_change_usd": city_delta - sum(row["overtime_change_usd"] for row in chosen),
            "overtime_pay_usd": sum(row["overtime_pay_usd"] for row in remaining),
            "share_of_city_overtime": sum(row["share_of_city_overtime"] for row in remaining),
            "overtime_share_of_department_pay": None,
        })
    chicago_latest = [row for row in chicago_elements if int(row["payroll_year"]) == latest]
    retro = sum((money(row, "amount") for row in chicago_latest if row["pay_element"] == "PR YR RETRO PEN"), Decimal())
    chicago_city = next(row for row in city_years if row["city"] == "Chicago" and row["year"] == latest)
    chicago_prior = next(row for row in city_years if row["city"] == "Chicago" and row["year"] == prior)
    sensitivity = [
        {"scenario": "Reported proxy", "year": latest, "overtime_share": chicago_city["overtime_share"], "excluded_amount_usd": 0.0},
        {"scenario": "Excluding PR YR RETRO PEN", "year": latest, "overtime_share": chicago_city["overtime_pay_usd"] / (chicago_city["total_pay_usd"] - as_float(retro)), "excluded_amount_usd": as_float(retro)},
        {"scenario": f"{prior} comparison", "year": prior, "overtime_share": chicago_prior["overtime_share"], "excluded_amount_usd": 0.0},
    ]
    driver_names = {city: {row["department"] for row in drivers if row["city"] == city and row["department"] != "All other departments"} for city in BASES}
    return {
        "version": 2,
        "metadata": {
            "retrieved_at_utc": retrieved_at, "included_years": years, "latest_complete_year": latest,
            "excluded_incomplete_years": sorted({int(row["payroll_year"]) for row in chicago_periods if int(row["periods"]) != CHICAGO_COMPLETE_PERIODS}),
            "headline_supported": len({tuple(sorted(names)) for names in driver_names.values()}) == len(BASES),
            "record_scope": "Aggregate municipal payroll only; no employee-level records are stored.",
        },
        "definitions": {
            "overtime_share": "Overtime pay divided by regular pay plus overtime pay plus other pay.",
            "department_driver": f"Department overtime pay in {latest} minus department overtime pay in {prior}.",
            "classification_note": "NYC and San Francisco use published overtime fields. Chicago overtime is an analyst-classified proxy based on pay-element names.",
        },
        "sources": [{"city": city, "dataset_url": SOURCE_PAGES[city], "api_url": BASES[city]} for city in BASES],
        "period_coverage": chicago_periods, "city_years": city_years, "department_years": departments,
        "top_departments": top_departments, "concentrations": concentrations, "drivers": drivers,
        "chicago_sensitivity": sensitivity,
    }


def validate_story(story: dict) -> None:
    years = story["metadata"]["included_years"]
    expected = {(city, year) for city in BASES for year in years}
    city_rows = story["city_years"]
    keys = {(row["city"], row["year"]) for row in city_rows}
    if keys != expected or len(keys) != len(city_rows):
        raise ValueError("City-year coverage contains missing or duplicate rows")
    for row in city_rows:
        total = row["regular_pay_usd"] + row["overtime_pay_usd"] + row["other_pay_usd"]
        if abs(total - row["total_pay_usd"]) > 0.02:
            raise ValueError(f"Pay components do not reconcile: {row['city']} {row['year']}")
        if any(not math.isfinite(value) for value in row.values() if isinstance(value, float)):
            raise ValueError(f"Non-finite value: {row['city']} {row['year']}")
    dept_totals: dict[tuple[str, int], dict[str, float]] = defaultdict(lambda: {"total": 0.0, "overtime": 0.0})
    for row in story["department_years"]:
        key = (row["city"], row["year"])
        dept_totals[key]["total"] += row["total_pay_usd"]
        dept_totals[key]["overtime"] += row["overtime_pay_usd"]
    city_lookup = {(row["city"], row["year"]): row for row in city_rows}
    for key, totals in dept_totals.items():
        city = city_lookup[key]
        if abs(totals["total"] - city["total_pay_usd"]) > 0.25 or abs(totals["overtime"] - city["overtime_pay_usd"]) > 0.25:
            raise ValueError(f"Department totals do not reconcile for {key}")
    latest = years[-1]
    for city in BASES:
        driver_sum = sum(row["overtime_change_usd"] for row in story["drivers"] if row["city"] == city)
        city_delta = next(row["overtime_change_usd"] for row in city_rows if row["city"] == city and row["year"] == latest)
        if abs(driver_sum - city_delta) > 0.25:
            raise ValueError(f"Driver contributions do not reconcile for {city}")


def main() -> None:
    retrieved_at = datetime.now(timezone.utc).isoformat()
    years, chicago_periods = discover_story_years()
    city_years, chicago_elements = build_city_years(years)
    departments = build_departments(years, city_years)
    story = build_story_data(years, city_years, departments, chicago_elements, chicago_periods, retrieved_at)
    validate_story(story)
    csv_write(OUT / "city_year_summary.csv", city_years)
    csv_write(OUT / "department_year.csv", departments)
    (OUT / "story_data.json").write_text(json.dumps(story, indent=2, ensure_ascii=False), encoding="utf-8")
    (OUT / "run_metadata.json").write_text(json.dumps({
        "retrieved_utc": retrieved_at, "included_years": years, "sources": BASES,
        "checks": "City-year components, department totals, Chicago periods, driver contributions, and sensitivity scenarios validated.",
    }, indent=2), encoding="utf-8")
    print(json.dumps({"included_years": years, "city_year_rows": len(city_years), "department_year_rows": len(departments), "retrieved_at_utc": retrieved_at}, indent=2))


if __name__ == "__main__":
    main()
