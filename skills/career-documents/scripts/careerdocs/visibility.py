"""Visibility filtering for renderers and exports.

The rules (from the provider contract and data model):

* ``private`` is never rendered and never exported.
* ``unverified`` facts never render.
* ``restricted`` renders into a document only when an approval names that document.
* an unresolved conflict is handled separately (``schema.unresolved_conflict_fields``).

A derived export keeps everything except ``private`` (it is a mirror the applicant owns);
a rendered document applies the full rules for a specific document. When an entity is
hidden, references to it are stripped and dependent achievements are dropped, so the
filtered profile stays internally consistent.
"""

from __future__ import annotations

_REFERENCE_LIST_FIELDS = ("achievement_ids", "skill_ids", "evidence_ids")


def approved_documents(approvals: list[dict]) -> set[str]:
    return {a["document"] for a in approvals if a.get("document")}


def is_visible(
    entity: dict,
    *,
    document: str | None = None,
    approved_docs=frozenset(),
    for_export: bool = False,
) -> bool:
    visibility = entity.get("visibility", "public")
    if visibility == "private":
        return False
    if for_export:
        return True
    if entity.get("verification") == "unverified":
        return False
    if visibility == "restricted":
        return document is not None and document in approved_docs
    return True


def filter_visible(
    profile: dict,
    *,
    document: str | None = None,
    approved_docs=frozenset(),
    for_export: bool = False,
) -> dict:
    entities = profile["entities"]
    visible = {
        e["id"]
        for e in entities
        if is_visible(e, document=document, approved_docs=approved_docs, for_export=for_export)
    }

    # Cascade: an achievement whose parent is hidden cannot survive.
    changed = True
    while changed:
        changed = False
        for entity in entities:
            if (
                entity["id"] in visible
                and entity["type"] == "achievement"
                and entity.get("parent_id") not in visible
            ):
                visible.discard(entity["id"])
                changed = True

    kept: list[dict] = []
    for entity in entities:
        if entity["id"] not in visible:
            continue
        pruned = dict(entity)
        for field in _REFERENCE_LIST_FIELDS:
            if field in pruned:
                pruned[field] = [ref for ref in pruned[field] if ref in visible]
        kept.append(pruned)
    return {**profile, "entities": kept}


def visible_entities(profile: dict, **kwargs) -> list[dict]:
    return filter_visible(profile, **kwargs)["entities"]
