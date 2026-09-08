"""Merge extracted candidates into ProfileDiff operations.

Candidates (the agent's extraction from sources) are deduplicated by a per-type match key,
reconciled by precedence, and turned into ``add_entity`` operations — with any field the
sources disagree on recorded as a conflict rather than silently overwritten. The result
feeds ``profile diff``; nothing is written until the applicant approves and applies.

Precedence when values differ: an applicant ``statement`` beats an ``applicant_verified``
import, which beats the newest plain import. The loser becomes a conflict candidate.
"""

from __future__ import annotations

import json
from collections import OrderedDict, defaultdict

from . import ids, util
from .errors import CareerDocsError

_META_KEYS = {
    "type", "provenance", "ref", "parent_ref", "verification", "visibility",
    "id", "conflicts", "created_at", "updated_at",
}


def norm(value) -> str:
    return " ".join(value.lower().split()) if value else ""


def match_key(candidate: dict):
    t = candidate["type"]
    if t == "experience":
        return (t, norm(candidate.get("organization")), norm(candidate.get("title")), (candidate.get("start_date") or "")[:4])
    if t == "education":
        return (t, norm(candidate.get("institution")), norm(candidate.get("degree")))
    if t == "skill":
        return (t, norm(candidate.get("name")))
    if t in ("credential", "patent", "publication"):
        return (t, candidate.get("number") or norm(candidate.get("title") or candidate.get("name")))
    if t == "project":
        return (t, norm(candidate.get("name")))
    if t == "contact":
        return (t,)
    if t == "achievement":
        return (t, candidate.get("parent_ref"), norm(candidate.get("statement")))
    return (t, id(candidate))


def _rank(candidate: dict) -> int:
    method = candidate.get("provenance", {}).get("method")
    if method == "statement":
        return 3
    if candidate.get("verification") == "applicant_verified":
        return 2
    return 1


def _verification(group: list[dict]) -> str:
    if any(c.get("provenance", {}).get("method") == "statement" for c in group):
        return "applicant_verified"
    if any(c.get("verification") == "applicant_verified" for c in group):
        return "applicant_verified"
    return "imported"


def _merge_group(group: list[dict]) -> tuple[dict, list[dict]]:
    ranked = sorted(group, key=lambda c: (_rank(c), c["provenance"]["recorded_at"]), reverse=True)
    entity = {
        "type": group[0]["type"],
        "visibility": next((c.get("visibility") for c in ranked if c.get("visibility")), "public"),
        "verification": _verification(group),
        "provenance": [c["provenance"] for c in group],
        "created_at": util.now(),
        "updated_at": util.now(),
    }
    conflicts: list[dict] = []
    field_values: "OrderedDict[str, list]" = OrderedDict()
    for candidate in ranked:
        for key, value in candidate.items():
            if key in _META_KEYS:
                continue
            field_values.setdefault(key, []).append((value, candidate))

    for field, pairs in field_values.items():
        distinct: "OrderedDict[str, tuple]" = OrderedDict()
        for value, candidate in pairs:
            distinct.setdefault(json.dumps(value, sort_keys=True), (value, candidate))
        entity[field] = pairs[0][0]  # highest-precedence value (ranked order)
        if len(distinct) > 1:
            conflicts.append({
                "field": field,
                "candidates": [
                    {"value": value, "provenance": candidate["provenance"]}
                    for value, candidate in distinct.values()
                ],
            })
    return entity, conflicts


def build_operations(profile: dict, payload) -> list[dict]:
    candidates = payload["candidates"] if isinstance(payload, dict) else payload
    existing_by_key = {match_key(e): e for e in profile["entities"]}

    groups: "OrderedDict[tuple, list]" = OrderedDict()
    achievements: list[dict] = []
    for candidate in candidates:
        if candidate["type"] == "achievement":
            achievements.append(candidate)
        else:
            groups.setdefault(match_key(candidate), []).append(candidate)

    operations: list[dict] = []
    ref_to_id: dict[str, str] = {}

    for key, group in groups.items():
        entity, conflicts = _merge_group(group)
        existing = existing_by_key.get(key)
        if existing is not None:
            entity_id = existing["id"]
            winner_provenance = entity["provenance"][-1]
            for field, value in entity.items():
                if field in ("provenance", "created_at", "updated_at", "type"):
                    continue
                if existing.get(field) != value:
                    operations.append({
                        "op": "update_field", "id": entity_id, "field": field,
                        "from": existing.get(field), "to": value, "provenance": winner_provenance,
                    })
        else:
            entity_id = ids.new_id(entity["type"])
            entity["id"] = entity_id
            if conflicts:
                entity["conflicts"] = conflicts
            operations.append({"op": "add_entity", "entity": entity})
        for candidate in group:
            if candidate.get("ref"):
                ref_to_id[candidate["ref"]] = entity_id

    achievement_groups: "OrderedDict[tuple, list]" = OrderedDict()
    for candidate in achievements:
        achievement_groups.setdefault((candidate.get("parent_ref"), norm(candidate.get("statement"))), []).append(candidate)

    parent_to_new_achievements: dict[str, list[str]] = defaultdict(list)
    for _, group in achievement_groups.items():
        entity, conflicts = _merge_group(group)
        parent_ref = group[0].get("parent_ref")
        parent_id = ref_to_id.get(parent_ref)
        if parent_id is None:
            raise CareerDocsError(f"achievement parent_ref {parent_ref!r} does not resolve to an experience or project")
        entity["parent_id"] = parent_id
        entity_id = ids.new_id("achievement")
        entity["id"] = entity_id
        if conflicts:
            entity["conflicts"] = conflicts
        operations.append({"op": "add_entity", "entity": entity})
        parent_to_new_achievements[parent_id].append(entity_id)

    for op in operations:
        if op["op"] == "add_entity" and op["entity"]["type"] in ("experience", "project"):
            new_ids = parent_to_new_achievements.get(op["entity"]["id"])
            if new_ids:
                op["entity"].setdefault("achievement_ids", []).extend(new_ids)

    return operations
