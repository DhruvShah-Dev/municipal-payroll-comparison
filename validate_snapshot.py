"""Validate the committed public-data snapshot without network access.

Run: python validate_snapshot.py
"""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from decimal import Decimal
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
EXPECTED_CITIES = {"Chicago", "New York City", "San Francisco"}
EXPECTED_YEARS = {"2024", "2025"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def read_csv(name: str) -> list[dict[str, str]]:
    with (DATA / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class PageLinks(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.navigation: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "a" and values.get("class") == "metro-payroll-page-nav":
            self.navigation.append(values.get("href") or "")


def main() -> None:
    rows = read_csv("city_year_summary.csv")
    require(len(rows) == 6, "Expected two annual rows for each of three cities")
    keys = {(r["city"], r["year"]) for r in rows}
    require(keys == {(city, year) for city in EXPECTED_CITIES for year in EXPECTED_YEARS},
            "City-year coverage changed")
    for row in rows:
        total = Decimal(row["total_pay_usd"])
        components = sum((Decimal(row[key]) for key in
                          ("regular_pay_usd", "overtime_pay_usd", "other_pay_usd")), Decimal())
        require(total > 0 and abs(total - components) <= Decimal("0.01"),
                f"Pay components do not reconcile for {row['city']} {row['year']}")
        share = Decimal(row["overtime_pay_usd"]) / total * 100
        require(abs(share - Decimal(row["overtime_share_pct"])) < Decimal("0.0001"),
                f"Overtime share does not reconcile for {row['city']} {row['year']}")

    departments = read_csv("department_2025.csv")
    totals: dict[str, dict[str, Decimal]] = defaultdict(lambda: defaultdict(Decimal))
    for row in departments:
        require(row["city"] in EXPECTED_CITIES, f"Unexpected city: {row['city']}")
        require(row["department"].strip() != "", "Blank department")
        for field in ("total_pay_usd", "overtime_pay_usd"):
            totals[row["city"]][field] += Decimal(row[field])
    for row in rows:
        if row["year"] != "2025":
            continue
        for field in ("total_pay_usd", "overtime_pay_usd"):
            require(abs(totals[row["city"]][field] - Decimal(row[field])) <= Decimal("0.10"),
                    f"Department subtotal differs for {row['city']}: {field}")

    raw = json.loads((DATA / "source_aggregates.json").read_text(encoding="utf-8"))
    periods = raw["chicago_periods"]
    require({(p["payroll_year"], p["first_period"], p["last_period"], p["periods"])
             for p in periods} == {("2024", "1", "24", "24"), ("2025", "1", "24", "24")},
            "Chicago payroll-period coverage changed")

    for html_name, artifact_name, next_page in (
        ("report.html", "artifact.json", "comparison.html"),
        ("comparison.html", "comparison_artifact.json", "report.html"),
    ):
        artifact = json.loads((ROOT / artifact_name).read_text(encoding="utf-8"))
        require(artifact["surface"] == "report" and artifact["snapshot"]["status"] == "ready",
                f"{artifact_name} is not a ready report")
        require(len(artifact["manifest"]["charts"]) >= 2, f"{artifact_name} lost its charts")
        parser = PageLinks()
        parser.feed((ROOT / html_name).read_text(encoding="utf-8"))
        require(parser.navigation == [next_page] and (ROOT / next_page).is_file(),
                f"{html_name} navigation is broken")

    print("Snapshot validation passed: six city-year rows, reconciled totals, complete Chicago periods, and two linked report pages.")


if __name__ == "__main__":
    main()
