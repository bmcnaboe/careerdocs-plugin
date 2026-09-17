"""Pagination check: a résumé reaches its target; other documents fit their budget."""

from __future__ import annotations

from pathlib import Path


def page_count(pdf_path) -> int:
    import pypdf

    return len(pypdf.PdfReader(str(Path(pdf_path))).pages)


def check(pdf_path, page_budget: int, *, exact: bool = False) -> dict:
    pages = page_count(pdf_path)
    if exact and pages != page_budget:
        return {"status": "fail", "details": f"{pages} page(s); résumé target is {page_budget}"}
    if pages > page_budget:
        return {"status": "fail", "details": f"{pages} pages exceed the budget of {page_budget}"}
    return {"status": "pass", "details": (
        f"{pages} page(s) match the résumé target" if exact
        else f"{pages} page(s) within the budget of {page_budget}"
    )}
