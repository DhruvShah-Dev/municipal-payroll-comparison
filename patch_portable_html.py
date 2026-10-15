"""Add local two-page navigation and a narrow portable-reader width correction.

Run after the Data Analytics portable HTML builder. This changes presentation
only; the embedded, validated artifact and chart runtime remain untouched.
"""

from __future__ import annotations

import sys
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PAGES = {
    "report.html": ("comparison.html", "Next page: comparison →", "next"),
    "comparison.html": ("report.html", "← Summary report", "prev"),
}


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in PAGES:
        raise SystemExit("Usage: python patch_portable_html.py report.html|comparison.html")
    name = sys.argv[1]
    target, label, relation = PAGES[name]
    page = ROOT / name
    html = page.read_text(encoding="utf-8")
    marker = "<!-- metro-payroll-page-nav -->"
    if marker in html:
        raise SystemExit(f"{name} already has page navigation; rebuild it before patching")
    if "</head>" not in html or "<body>" not in html:
        raise SystemExit(f"{name} is missing the expected portable HTML structure")
    style = """<style>
.analytics-top-bar{width:100%!important;margin-left:0!important;margin-right:0!important}
.metro-payroll-page-nav{position:fixed;right:18px;bottom:18px;z-index:80;max-width:calc(100vw - 36px);padding:10px 15px;border-radius:999px;background:#114b79;color:#fff;font:600 13px/1.3 system-ui,sans-serif;text-decoration:none;box-shadow:0 3px 12px rgba(0,0,0,.2)}
.metro-payroll-page-nav:hover{background:#0a3658;color:#fff}
.metro-payroll-page-nav:focus-visible{outline:3px solid #e3a842;outline-offset:3px}
@media print{.metro-payroll-page-nav{display:none}}
</style>"""
    nav = f'{marker}<a class="metro-payroll-page-nav" href="{escape(target)}" rel="{relation}">{escape(label)}</a>'
    html = html.replace("</head>", style + "</head>", 1).replace("<body>", "<body>" + nav, 1)
    page.write_text(html, encoding="utf-8")
    print(f"Patched {page}")


if __name__ == "__main__":
    main()
