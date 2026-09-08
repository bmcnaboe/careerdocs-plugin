"""Pagination check: the PDF must fit its page budget."""

from __future__ import annotations

from pathlib import Path


def page_count(pdf_path) -> int:
    import pypdf

    return len(pypdf.PdfReader(str(Path(pdf_path))).pages)


def check(pdf_path, page_budget: int) -> dict:
    pages = page_count(pdf_path)
    if pages > page_budget:
        return {"status": "fail", "details": f"{pages} pages exceed the budget of {page_budget}"}
    return {"status": "pass", "details": f"{pages} page(s) within the budget of {page_budget}"}
