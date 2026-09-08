"""Extract experience candidates from a positions/connections CSV export.

A network export is structured, so each row with a company and a title becomes an
experience candidate directly (still a proposal — nothing is written to the profile).
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

from .. import util

_DATE_RE = re.compile(r"^\d{4}-\d{2}(-\d{2})?$")
_COMPANY_KEYS = ("Company", "company", "Organization", "organization")
_TITLE_KEYS = ("Title", "title", "Position", "position")
_START_KEYS = ("Started On", "Started", "start_date", "Start Date")
_END_KEYS = ("Finished On", "Finished", "end_date", "End Date")


def _first(row: dict, keys) -> str | None:
    for key in keys:
        value = row.get(key)
        if value and value.strip():
            return value.strip()
    return None


def _norm_date(value: str | None) -> str | None:
    return value if value and _DATE_RE.match(value) else None


def extract(path, source_id: str) -> dict:
    blocks: list[str] = []
    candidates: list[dict] = []
    with open(Path(path), newline="", encoding="utf-8") as fh:
        for index, row in enumerate(csv.DictReader(fh)):
            block = ", ".join(f"{k}: {v}" for k, v in row.items() if v)
            blocks.append(block)
            organization = _first(row, _COMPANY_KEYS)
            title = _first(row, _TITLE_KEYS)
            if not (organization and title):
                continue
            candidate = {
                "type": "experience",
                "ref": f"net-{index}",
                "provenance": {
                    "source_id": source_id,
                    "method": "extraction",
                    "recorded_at": util.now(),
                    "actor": "agent",
                    "excerpt": block,
                },
                "organization": organization,
                "title": title,
            }
            start = _norm_date(_first(row, _START_KEYS))
            end = _norm_date(_first(row, _END_KEYS))
            if start:
                candidate["start_date"] = start
            if end:
                candidate["end_date"] = end
            candidates.append(candidate)
    return {"text_blocks": blocks, "candidates": candidates}
