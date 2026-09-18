"""Factual traceability check.

Every content line of the rendered document must be a plan unit — or one line of a
multi-line unit, such as the contact unit's name and details lines — or a
template-provided string on the allowlist, or a line the render composed from the role
brief and the calendar (recorded as the output's ``template_lines``), and every number
and date in the document must trace to one of the entities the plan cites or to one of
those lines. This is what stops invented qualifications
and altered metrics from reaching a document.
"""

from __future__ import annotations

import re

_NUMBER_RE = re.compile(r"\d[\d,]*(?:\.\d+)?")


def _blob(entity: dict) -> str:
    parts: list[str] = []

    def walk(value):
        if isinstance(value, str):
            parts.append(value)
        elif isinstance(value, dict):
            for item in value.values():
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(entity)
    return " ".join(parts)


def _squash(text: str) -> str:
    return " ".join(text.split())


def cited_entity_ids(plan: dict) -> set[str]:
    return {sid for unit in plan["units"] for sid in unit["source_ids"]}


def digits_of(lines) -> set[str]:
    """The digit groups in ``lines``, in the form the number check compares against."""
    return set(re.sub(r"\D", " ", " ".join(lines)).split())


def check(document_text: str, plan: dict, profile: dict, allowlist=(), template_lines=()) -> dict:
    """``allowlist`` holds the template's fixed strings; ``template_lines`` the lines the
    render composed from the role brief and the calendar (a letter's role line and date),
    whose numbers need no entity behind them."""
    by_id = {e["id"]: e for e in profile["entities"]}
    cited = cited_entity_ids(plan)
    blob = " ".join(_blob(by_id[i]) for i in cited if i in by_id)
    blob_digits = digits_of([blob]) | digits_of(template_lines)
    # Lines compare with their whitespace collapsed: a template may set a unit's tab as a
    # gap or a tab stop, and PDF extraction respaces text.
    allowed_lines = {_squash(line) for line in (*allowlist, *template_lines)}
    for unit in plan["units"]:
        allowed_lines.add(_squash(unit["text"]))
        allowed_lines.update(_squash(line) for line in unit["text"].splitlines())

    findings: list[str] = []
    for line in (_squash(line) for line in document_text.splitlines()):
        if not line or line in allowed_lines:
            continue
        findings.append(f"unsourced line: {line!r}")

    for match in _NUMBER_RE.findall(document_text):
        integer_part = match.replace(",", "").split(".")[0]
        if integer_part and integer_part not in blob_digits:
            findings.append(f"untraceable number: {match}")

    if findings:
        return {"status": "fail", "details": "; ".join(findings)}
    return {"status": "pass", "details": "every unit and number traces to a cited entity"}


_VERBATIM_MIN_LEN = 15


def verbatim_bullet_check(document_text: str, resume_bullets) -> dict:
    """Flag any résumé bullet reproduced verbatim in the (cover-letter) document.

    A cover letter must complement the résumé, not repeat it; a bullet appearing verbatim
    (as a line or embedded in a sentence) fails the check.
    """
    findings: list[str] = []
    for bullet in resume_bullets:
        text = bullet.strip()
        if len(text) >= _VERBATIM_MIN_LEN and text in document_text:
            findings.append(f"verbatim résumé bullet reused: {text!r}")
    if findings:
        return {"status": "fail", "details": "; ".join(findings)}
    return {"status": "pass", "details": "no résumé bullet reproduced verbatim"}
