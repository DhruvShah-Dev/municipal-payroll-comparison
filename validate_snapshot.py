"""Validate the committed aggregate snapshot without network access."""

from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
EXPECTED_CITIES = {"Chicago", "New York City", "San Francisco"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> None:
    story = json.loads((DATA / "story_data.json").read_text(encoding="utf-8"))
    years = story["metadata"]["included_years"]
    require(len(years) == 3 and years == sorted(years), "Expected three ordered complete years")
    require(story["metadata"]["latest_complete_year"] == years[-1], "Latest year metadata is inconsistent")
    require(years[-1] not in story["metadata"]["excluded_incomplete_years"], "Included year is marked incomplete")

    city_rows = story["city_years"]
    expected_keys = {(city, year) for city in EXPECTED_CITIES for year in years}
    actual_keys = {(row["city"], row["year"]) for row in city_rows}
    require(len(city_rows) == 9 and actual_keys == expected_keys, "City-year coverage is incomplete or duplicated")
    city_lookup = {(row["city"], row["year"]): row for row in city_rows}
    for row in city_rows:
        total = row["regular_pay_usd"] + row["overtime_pay_usd"] + row["other_pay_usd"]
        require(abs(total - row["total_pay_usd"]) <= 0.02, f"Pay components do not reconcile for {row['city']} {row['year']}")
        require(abs(row["overtime_pay_usd"] / row["total_pay_usd"] - row["overtime_share"]) < 1e-12, f"Overtime share does not reconcile for {row['city']} {row['year']}")
        require(all(math.isfinite(value) for value in row.values() if isinstance(value, float)), f"Non-finite value for {row['city']} {row['year']}")

    complete_chicago = {
        int(row["payroll_year"]) for row in story["period_coverage"]
        if int(row["periods"]) == 24 and int(row["first_period"]) == 1 and int(row["last_period"]) == 24
    }
    require(set(years).issubset(complete_chicago), "Chicago does not contain all 24 periods for every included year")

    department_totals: dict[tuple[str, int], dict[str, float]] = defaultdict(lambda: {"total": 0.0, "overtime": 0.0})
    for row in story["department_years"]:
        require(row["department"].strip() != "", "Blank department label")
        key = (row["city"], row["year"])
        department_totals[key]["total"] += row["total_pay_usd"]
        department_totals[key]["overtime"] += row["overtime_pay_usd"]
    require(set(department_totals) == expected_keys, "Department coverage differs from city-year coverage")
    for key, totals in department_totals.items():
        city = city_lookup[key]
        require(abs(totals["total"] - city["total_pay_usd"]) <= 0.25, f"Department total pay differs for {key}")
        require(abs(totals["overtime"] - city["overtime_pay_usd"]) <= 0.25, f"Department overtime differs for {key}")

    latest = years[-1]
    for city in EXPECTED_CITIES:
        driver_total = sum(row["overtime_change_usd"] for row in story["drivers"] if row["city"] == city)
        city_change = city_lookup[(city, latest)]["overtime_change_usd"]
        require(abs(driver_total - city_change) <= 0.25, f"Driver contributions do not reconcile for {city}")
        top = [row for row in story["top_departments"] if row["city"] == city]
        require(len(top) == 5 and {row["rank"] for row in top} == {1, 2, 3, 4, 5}, f"Top-five ranking is invalid for {city}")

    sensitivity = story["chicago_sensitivity"]
    require(len(sensitivity) == 3, "Chicago sensitivity scenarios changed")
    require(sensitivity[0]["overtime_share"] < sensitivity[2]["overtime_share"], "Chicago direction of change is not preserved")
    require(sensitivity[0]["overtime_share"] < sensitivity[1]["overtime_share"] < sensitivity[2]["overtime_share"], "Chicago sensitivity ordering is invalid")
    require(sensitivity[1]["excluded_amount_usd"] > 0, "Chicago sensitivity exclusion is missing")

    for redirect in (ROOT / "report.html", ROOT / "comparison.html"):
        require(redirect.is_file(), f"Missing compatibility page: {redirect.name}")

    print(f"Snapshot validation passed: 9 city-year rows across {years[0]}–{years[-1]}, reconciled departments and drivers, complete Chicago periods, and valid sensitivity scenarios.")


if __name__ == "__main__":
    main()
