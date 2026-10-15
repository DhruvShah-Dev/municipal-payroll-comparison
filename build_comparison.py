"""Build the second, detailed comparison page from reviewed aggregate CSVs."""

from __future__ import annotations

import csv
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
base = json.loads((ROOT / "artifact.json").read_text(encoding="utf-8"))
summary = list(csv.DictReader((DATA / "city_year_summary.csv").open(encoding="utf-8")))
departments = list(csv.DictReader((DATA / "department_2025.csv").open(encoding="utf-8")))
metadata = json.loads((DATA / "run_metadata.json").read_text(encoding="utf-8"))
db = sqlite3.connect(":memory:")
db.row_factory = sqlite3.Row
for table, rows in (("city_year_summary", summary), ("department_2025", departments)):
    cols = list(rows[0])
    db.execute(f"CREATE TABLE {table} ({', '.join(col + ' TEXT' for col in cols)})")
    db.executemany(f"INSERT INTO {table} VALUES ({', '.join('?' for _ in cols)})",
                   ([row[col] for col in cols] for row in rows))


def sql_dataset(name: str) -> tuple[str, list[dict]]:
    sql = (ROOT / "queries" / f"{name}.sql").read_text(encoding="utf-8")
    return sql, [dict(row) for row in db.execute(sql)]


mix_sql, mix = sql_dataset("pay_mix")
compare_sql, compare = sql_dataset("city_comparison")
top_sql, top = sql_dataset("top_departments")
assert len(mix) == 9 and len(compare) == 3 and len(top) == 15
compare_by_city = {r["city"]: r for r in compare}
top5_share = {city: sum(r["share_of_city_overtime"] for r in top if r["city"] == city)
              for city in compare_by_city}


def source(name: str, label: str, sql: str, tables: list[str]) -> dict:
    return {"id": name, "label": label, "path": f"queries/{name}.sql", "tables_used": tables,
            "query": {"engine": "SQLite over Socrata aggregates", "language": "sql", "sql": sql,
                      "description": "Query the reviewed aggregate CSVs created from three official municipal open-data APIs by analyze.py.",
                      "executed_at": metadata["retrieved_utc"]}}


city_tables = ["data.cityofnewyork.us.k397-673e", "data.cityofchicago.org.dawh-m56b",
               "data.sf.gov.88g8-5mnd"]
sources = base["sources"] + [
    source("pay_mix", "2025 pay mix by city", mix_sql, city_tables),
    source("city_comparison", "2025 city comparison and 2024 baseline", compare_sql, city_tables),
    source("top_departments", "Top five overtime departments in each city", top_sql, city_tables),
]
title = "Three-city payroll comparison: details"
chicago = compare_by_city["Chicago"]
nyc = compare_by_city["New York City"]
sf = compare_by_city["San Francisco"]

blocks = [
    {"id": "title", "type": "markdown", "body": f"# {title}"},
    {"id": "summary", "type": "markdown", "sourceId": "city_comparison",
     "body": "## Executive Summary\n\n- **Overtime is a meaningful part of pay in all three city governments.** In 2025 it represented 8.4% of reported pay in New York City, 9.0% in San Francisco, and an estimated 10.7% in Chicago.\n- **Overtime share decreased in each city from 2024.** Chicago had the largest percentage-point drop, though its pay elements and payroll calendar differ from the two fiscal-year datasets.\n- **Most overtime dollars are concentrated in a few departments.** Police and fire are major contributors in every city, but the department mix differs enough that these shares cannot measure staffing efficiency on their own."},
    {"id": "basis", "type": "markdown", "sourceId": "city_comparison",
     "body": "## How to read this page\n\nThe comparison covers municipal payroll, not all jobs in each metropolitan area. **Reported pay** equals regular pay, overtime pay, and other pay; San Francisco benefits are excluded. **Overtime share** is overtime divided by reported pay. NYC and San Francisco publish overtime directly for fiscal years ending June 30. Chicago records employee pay elements across 24 payroll periods; its overtime amount is an analyst-defined classification. Compare patterns within each city first, then use the cross-city figures as descriptive context."},
    {"id": "mix_intro", "type": "markdown", "sourceId": "pay_mix",
     "body": "## Regular pay dominates, but the mix differs\n\nThe chart divides each city's 2025 reported pay into regular, overtime, and other pay. Chicago has a larger overtime and other-pay share under its pay-element classification. Its `PR YR RETRO PEN` element alone contributed about $161 million to 2025 other pay. San Francisco's retirement and health benefits are excluded, so the chart compares salary-related amounts rather than total employer compensation."},
    {"id": "mix_chart", "type": "chart", "chartId": "mix_chart"},
    {"id": "movement_intro", "type": "markdown", "sourceId": "city_comparison",
     "body": f"## Overtime share fell in each source\n\nFrom 2024 to 2025, Chicago fell **{abs(chicago['share_change_pp']):.2f} percentage points**, San Francisco **{abs(sf['share_change_pp']):.2f} points**, and New York City **{abs(nyc['share_change_pp']):.2f} points**. Chicago overtime dollars fell {abs(chicago['overtime_dollar_change'])*100:.1f}%, while San Francisco's rose slightly despite a lower share because its total salary pay grew. The side-by-side chart shows both years without suggesting the fiscal and payroll windows are identical."},
    {"id": "movement_chart", "type": "chart", "chartId": "overtime_share_chart"},
    {"id": "numbers_intro", "type": "markdown", "sourceId": "city_comparison",
     "body": "## Exact 2025 measures\n\nNew York City's reported salary pay is far larger in absolute dollars, reflecting a different workforce scale and service scope. The table keeps dollars and shares together so a large payroll is not mistaken for a high overtime rate. The year-over-year column is a change in **percentage points**, calculated within each city's own dataset."},
    {"id": "numbers_table", "type": "table", "tableId": "city_table"},
    {"id": "service_intro", "type": "markdown", "sourceId": "departments",
     "body": "## Public safety is a major overtime user\n\nPolice and fire together account for about **73%** of Chicago overtime, **57%** of New York City overtime, and **46%** of San Francisco overtime in 2025. The chart shows each department's share of its own city's overtime total. San Francisco also publishes sheriff and transit overtime separately; NYC corrections and sanitation are large overtime users. These differences in service organization affect the comparison."},
    {"id": "service_chart", "type": "chart", "chartId": "service_share_chart"},
    {"id": "top_intro", "type": "markdown", "sourceId": "top_departments",
     "body": f"## Five departments account for most overtime\n\nThe top five departments account for **{top5_share['Chicago']*100:.1f}%** of Chicago overtime, **{top5_share['New York City']*100:.1f}%** in New York City, and **{top5_share['San Francisco']*100:.1f}%** in San Francisco. The table identifies the departments and distinguishes each one's share of city overtime from overtime as a share of that department's own pay. Department labels are published labels and have not been forced into a single cross-city taxonomy."},
    {"id": "top_table", "type": "table", "tableId": "department_table"},
    {"id": "interpretation", "type": "markdown", "sourceId": "city_comparison",
     "body": "## What the figures can and cannot tell us\n\nThe strongest common finding is the **within-city decline in overtime share**. Chicago's 2025 denominator includes a sizable prior-year retroactive pay element; removing only that $161 million item would raise its 2025 overtime share to about 11.1%, still below 2024. This one-item check supports the direction of change but does not settle every pay-element classification question. Differences in headcount, employee hours, contracts, staffing vacancies, emergencies, and agency responsibilities remain unmeasured here. Do not read the cross-city ranking as a productivity or fairness verdict."},
    {"id": "next", "type": "markdown",
     "body": "## Recommended next steps\n\n1. Investigate the largest overtime departments within each city over more complete years.\n2. Add full-time-equivalent staffing and worked hours for the same reporting windows before comparing operating efficiency.\n3. Obtain an official Chicago pay-element map and rerun the overtime classification sensitivity check."},
    {"id": "questions", "type": "markdown",
     "body": "## Further questions\n\nWhich departments explain most of the overtime decline? Did staffing vacancies, negotiated retroactive payments, or service demand change? Which services have sufficiently similar scope for a defensible cross-city comparison?"},
    {"id": "caveats", "type": "markdown", "sourceId": "city_comparison",
     "body": "## Caveats and assumptions\n\nSource snapshot retrieved October 15, 2026. NYC and San Francisco use fiscal years ending June 30; Chicago's 24 payroll periods may not match the actual dates worked. Chicago's published extract is unaudited and can be revised. It contains pay elements that the analyst mapped into regular, overtime, and other; classification uncertainty is concentrated there. San Francisco may have multiple rows per employee per year, so none of the source row counts are used as comparable headcounts. Benefits, taxes, deductions, and net pay are outside the shared comparison. This page describes city-government payroll rather than entire metro labor markets."},
]

charts = [
    {"id": "mix_chart", "title": "Composition of reported pay", "subtitle": "2025; shares of each city's own reported pay", "showDescription": True,
     "type": "stackedBar100", "dataset": "pay_mix", "sourceId": "pay_mix", "valueFormat": "percent",
     "encodings": {"x": {"field": "city", "type": "nominal", "label": "City"},
                   "y": {"field": "share", "type": "quantitative", "label": "Share of pay", "format": "percent"},
                   "color": {"field": "component", "type": "nominal", "label": "Pay component"},
                   "tooltip": [{"field": "amount_billion_usd", "type": "quantitative", "label": "Amount (USD billions)"}]},
     "settings": {"groupMode": "stacked100"}, "layout": "full"},
    next(c for c in base["manifest"]["charts"] if c["id"] == "overtime_share_chart"),
    next(c for c in base["manifest"]["charts"] if c["id"] == "service_share_chart"),
]
tables = [
    {"id": "city_table", "title": "2025 payroll comparison", "subtitle": "USD billions; 2024–2025 change in overtime share is in percentage points", "showDescription": True,
     "dataset": "city_comparison", "sourceId": "city_comparison",
     "columns": [{"field": "city", "label": "City", "type": "text"},
                 {"field": "basis", "label": "Reporting basis", "type": "text"},
                 {"field": "total_pay_billion_usd", "label": "Total pay ($B)", "type": "number"},
                 {"field": "overtime_pay_billion_usd", "label": "OT pay ($B)", "type": "number"},
                 {"field": "overtime_share", "label": "OT share", "format": "percent"},
                 {"field": "share_change_pp", "label": "Change (pp)", "type": "number", "movement": True}]},
    {"id": "department_table", "title": "Top five overtime departments in each city", "subtitle": "2025 overtime in USD millions and percentages of city overtime and department pay", "showDescription": True,
     "dataset": "top_departments", "sourceId": "top_departments",
     "columns": [{"field": "city", "label": "City", "type": "text"},
                 {"field": "rank", "label": "Rank", "type": "number"},
                 {"field": "department", "label": "Department", "type": "text"},
                 {"field": "overtime_million_usd", "label": "OT ($M)", "type": "number"},
                 {"field": "share_of_city_overtime", "label": "Of city OT", "format": "percent"},
                 {"field": "share_of_department_pay", "label": "Of dept pay", "format": "percent"}]},
]

artifact = {
    "surface": "report",
    "manifest": {"version": 1, "surface": "report", "title": title,
                 "description": "Detailed comparative analysis of official municipal payroll aggregates for 2024–2025.",
                 "generatedAt": datetime.now(timezone.utc).isoformat(),
                 "charts": charts, "tables": tables, "sources": sources, "blocks": blocks},
    "snapshot": {"version": 1, "status": "ready", "generatedAt": datetime.now(timezone.utc).isoformat(),
                 "datasets": {"pay_mix": mix, "city_comparison": compare, "top_departments": top,
                              "city_year": base["snapshot"]["datasets"]["city_year"],
                              "service_share": base["snapshot"]["datasets"]["service_share"]}},
    "sources": sources,
}
(ROOT / "comparison_artifact.json").write_text(json.dumps(artifact, indent=2), encoding="utf-8")
print(f"Wrote {ROOT / 'comparison_artifact.json'}")
