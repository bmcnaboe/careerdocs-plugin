"""Profile validation: JSON Schema plus the semantic rules the schema cannot express.

Structural validation runs against the shipped ``career-profile.schema.json``. On top of
that this module enforces the rules from the data model: end dates not before start
dates, no date in the future, every id reference resolving (and ``parent_id`` pointing at
an experience or project), and exactly one contact. It also exposes which fields are
blocked by an unresolved conflict, so renderers can omit them.
"""

from __future__ import annotations

import json
from datetime import date

import jsonschema

from . import paths
from .errors import ProfileInvalid

# date fields per entity type, and the (earlier, later) pairs that must be ordered.
DATE_FIELDS: dict[str, tuple[str, ...]] = {
    "experience": ("start_date", "end_date"),
    "education": ("start_date", "end_date"),
    "project": ("start_date", "end_date"),
    "credential": ("issued_date", "expires_date"),
    "patent": ("filing_date", "grant_date"),
    "publication": ("date",),
}
ORDER_PAIRS: dict[str, tuple[tuple[str, str], ...]] = {
    "experience": (("start_date", "end_date"),),
    "education": (("start_date", "end_date"),),
    "project": (("start_date", "end_date"),),
    "credential": (("issued_date", "expires_date"),),
    "patent": (("filing_date", "grant_date"),),
}
# id-reference fields; a value of None means "any entity type is acceptable".
REF_FIELDS: dict[str, dict[str, set[str] | None]] = {
    "experience": {"achievement_ids": {"achievement"}, "skill_ids": {"skill"}},
    "achievement": {"skill_ids": {"skill"}},
    "skill": {"evidence_ids": None},
    "project": {"achievement_ids": {"achievement"}},
}


def load_schema(name: str) -> dict:
    return json.loads((paths.SCHEMAS_DIR / f"{name}.schema.json").read_text(encoding="utf-8"))


def _validator(name: str) -> jsonschema.Draft202012Validator:
    schema = load_schema(name)
    # The shipped schemas encode a version in the $id fragment, which is not a valid base
    # URI; strip it so internal $ref resolution works, and skip the metaschema self-check.
    if isinstance(schema.get("$id"), str) and "#" in schema["$id"]:
        schema = dict(schema)
        schema["$id"] = schema["$id"].split("#", 1)[0]
    return jsonschema.Draft202012Validator(schema)


def validate_against(name: str, data) -> list[str]:
    """Return structural errors validating ``data`` against a named shipped schema."""
    errors = []
    for err in sorted(_validator(name).iter_errors(data), key=lambda e: list(e.path)):
        loc = "/".join(str(p) for p in err.path)
        errors.append(f"{loc}: {err.message}" if loc else err.message)
    return errors


def profile_schema_version() -> str:
    identifier = load_schema("career-profile").get("$id", "")
    return identifier.split("#", 1)[1] if "#" in identifier else "unknown"


def parse_date(value: str) -> date:
    """Parse ``YYYY-MM-DD`` or ``YYYY-MM`` (day defaults to the 1st)."""
    parts = value.split("-")
    year = int(parts[0])
    month = int(parts[1]) if len(parts) > 1 else 1
    day = int(parts[2]) if len(parts) > 2 else 1
    return date(year, month, day)


def unresolved_conflict_fields(entity: dict) -> set[str]:
    """Fields of ``entity`` whose conflict has no resolution (blocked from rendering)."""
    return {
        conflict["field"]
        for conflict in entity.get("conflicts", [])
        if not conflict.get("resolution")
    }


def _semantic_errors(profile: dict) -> list[str]:
    errors: list[str] = []
    entities = profile["entities"]
    by_id = {e["id"]: e for e in entities}
    today = date.today()

    contacts = [e for e in entities if e["type"] == "contact"]
    if len(contacts) > 1:
        errors.append("more than one contact entity")
    if entities and not contacts:
        errors.append("profile has entities but no contact")

    for entity in entities:
        etype = entity["type"]
        eid = entity["id"]

        for field in DATE_FIELDS.get(etype, ()):
            value = entity.get(field)
            if value:
                if parse_date(value) > today:
                    errors.append(f"{eid}: {field} {value} is in the future")

        for earlier, later in ORDER_PAIRS.get(etype, ()):
            ev, lv = entity.get(earlier), entity.get(later)
            if ev and lv and parse_date(lv) < parse_date(ev):
                errors.append(f"{eid}: {later} {lv} is before {earlier} {ev}")

        if etype == "achievement":
            parent_id = entity.get("parent_id")
            parent = by_id.get(parent_id)
            if parent is None:
                errors.append(f"{eid}: parent_id {parent_id!r} does not resolve")
            elif parent["type"] not in ("experience", "project"):
                errors.append(f"{eid}: parent_id must be an experience or project")

        for field, allowed_types in REF_FIELDS.get(etype, {}).items():
            for ref in entity.get(field, []):
                target = by_id.get(ref)
                if target is None:
                    errors.append(f"{eid}: {field} {ref!r} does not resolve")
                elif allowed_types is not None and target["type"] not in allowed_types:
                    errors.append(
                        f"{eid}: {field} {ref!r} must reference {'/'.join(sorted(allowed_types))}"
                    )
    return errors


def validate_profile(profile: dict) -> list[str]:
    """Return every validation error (structural first, then semantic); empty = valid."""
    structural = validate_against("career-profile", profile)
    if structural:
        return [f"schema: {e}" for e in structural]
    return _semantic_errors(profile)


def assert_valid_profile(profile: dict) -> None:
    errors = validate_profile(profile)
    if errors:
        raise ProfileInvalid("profile is invalid: " + "; ".join(errors[:5]))
