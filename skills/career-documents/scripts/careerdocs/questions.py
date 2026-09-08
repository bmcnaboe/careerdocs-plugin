"""Material questions for the applicant, and their conversion to diff operations.

Questions are generated only when the answer changes the profile: an unresolved conflict,
a missing date, or an undecided visibility. Each question has a stable id derived from the
entity and field, so re-generating after a resume yields the same ids and the workflow
state never asks an answered question twice. Answers convert to ``resolve_conflict``,
``update_field``, or ``set_visibility`` operations.
"""

from __future__ import annotations

_DATE_FIELDS_BY_TYPE = {
    "experience": ("start_date", "end_date"),
    "project": ("start_date", "end_date"),
    "education": ("start_date", "end_date"),
}
_CURRENT_ANSWERS = {"current", "ongoing", "none", "n/a", ""}


def _label(entity: dict) -> str:
    for field in ("title", "name", "organization", "institution", "statement"):
        if entity.get(field):
            return str(entity[field])
    return entity.get("id", entity["type"])


def generate_questions(entities: list[dict]) -> list[dict]:
    questions: list[dict] = []
    for entity in entities:
        eid = entity["id"]
        label = _label(entity)

        conflicted_fields = set()
        for conflict in entity.get("conflicts", []):
            if conflict.get("resolution"):
                continue
            field = conflict["field"]
            conflicted_fields.add(field)
            options = [candidate["value"] for candidate in conflict["candidates"]]
            questions.append({
                "id": f"conflict:{eid}:{field}",
                "kind": "conflict",
                "entity_id": eid,
                "field": field,
                "text": f"{label}: which {field.replace('_', ' ')} is correct? Options: {options}",
                "options": options,
            })

        for field in _DATE_FIELDS_BY_TYPE.get(entity["type"], ()):
            # A field already in conflict is asked as a conflict, not as a missing date.
            if entity.get(field) or field in conflicted_fields:
                continue
            # A missing start date is always material; a missing end date may just mean current.
            prompt = "current or a date (YYYY-MM)" if field == "end_date" else "a date (YYYY-MM)"
            questions.append({
                "id": f"date:{eid}:{field}",
                "kind": "date",
                "entity_id": eid,
                "field": field,
                "text": f"{label}: what is the {field.replace('_', ' ')}? Answer {prompt}.",
            })

        if entity.get("visibility") in (None, ""):
            questions.append({
                "id": f"visibility:{eid}:visibility",
                "kind": "visibility",
                "entity_id": eid,
                "field": "visibility",
                "text": f"{label}: should this be public, restricted, or private?",
                "options": ["public", "restricted", "private"],
            })
    return questions


def answer_to_operation(question: dict, answer: str) -> dict | None:
    kind = question["kind"]
    eid = question["entity_id"]
    field = question["field"]
    if kind == "conflict":
        return {"op": "resolve_conflict", "id": eid, "field": field, "value": answer}
    if kind == "date":
        to = None if answer.strip().lower() in _CURRENT_ANSWERS else answer.strip()
        return {"op": "update_field", "id": eid, "field": field, "from": None, "to": to}
    if kind == "visibility":
        return {"op": "set_visibility", "id": eid, "visibility": answer.strip()}
    return None


def answered_map(state: dict) -> dict[str, str]:
    return {q["id"]: q["answer"] for q in state["questions"] if q["answer"] is not None}


def operations_from_answers(questions: list[dict], answered: dict[str, str]) -> list[dict]:
    operations: list[dict] = []
    for question in questions:
        answer = answered.get(question["id"])
        if answer is None:
            continue
        op = answer_to_operation(question, answer)
        if op is not None:
            operations.append(op)
    return operations
