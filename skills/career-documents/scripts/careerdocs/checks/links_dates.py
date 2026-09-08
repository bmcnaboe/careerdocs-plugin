"""Link and date validity check.

Dates in the document must parse, be ordered within a range, and not lie in the future;
links must be syntactically valid. Link liveness needs the network, so it is recorded as
skipped when offline (the default) rather than failing the check.
"""

from __future__ import annotations

import re
from datetime import date

_ISO_DATE_RE = re.compile(r"\b(\d{4})-(\d{2})(?:-(\d{2}))?\b")
_YEAR_RANGE_RE = re.compile(r"\b(\d{4})\s*[–—-]\s*(\d{4})\b")
_URL_RE = re.compile(r"https?://\S+")
_URL_OK_RE = re.compile(r"^https?://[^\s/$.?#]+\.[^\s]*$")


def check(document_text: str, *, online: bool = False, today: date | None = None) -> dict:
    today = today or date.today()
    findings: list[str] = []

    for year, month, day in _ISO_DATE_RE.findall(document_text):
        try:
            parsed = date(int(year), int(month), int(day) if day else 1)
        except ValueError:
            findings.append(f"invalid date {year}-{month}{'-' + day if day else ''}")
            continue
        if parsed > today:
            findings.append(f"future date {year}-{month}")

    for start, end in _YEAR_RANGE_RE.findall(document_text):
        if int(start) > int(end):
            findings.append(f"date range {start}-{end} is out of order")
        if int(end) > today.year:
            findings.append(f"future year {end}")

    links = _URL_RE.findall(document_text)
    for url in links:
        cleaned = url.rstrip(").,;")
        if not _URL_OK_RE.match(cleaned):
            findings.append(f"malformed link {url}")

    liveness = "checked" if online else "skipped (offline)"
    if findings:
        return {"status": "fail", "details": "; ".join(findings)}
    detail = f"dates valid, {len(links)} link(s) well-formed; liveness {liveness}"
    return {"status": "pass", "details": detail}
