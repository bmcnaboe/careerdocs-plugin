"""Tests for the content plan builder."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "skills" / "career-documents" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from careerdocs import ids, plan  # noqa: E402

NOW = "2024-01-01T00:00:00Z"


def entity(entity_type, **extra):
    e = {
        "id": ids.new_id(entity_type), "type": entity_type, "visibility": "public",
        "verification": "applicant_verified",
        "provenance": [{"source_id": ids.new_source_id(), "method": "import", "recorded_at": NOW, "actor": "a"}],
        "created_at": NOW, "updated_at": NOW,
    }
    e.update(extra)
    return e


def profile_with(entities):
    return {"schema_version": "1.0.0", "applicant_ref": "a", "authoritative_provider": "markdown",
            "derived": False, "updated_at": NOW, "entities": entities, "sources": []}


def map_all_direct(entities):
    return [{"requirement_id": f"req-{i}", "classification": "direct",
             "evidence": [{"entity_id": e["id"], "why": "x"}], "note": ""}
            for i, e in enumerate(entities, start=1)]


EXPERIENCE_SECTION = {"id": "experience", "entity_types": ["experience"], "max_items": 10}


def test_units_carry_source_ids():
    exp = entity("experience", organization="Acme", title="Eng", start_date="2020-01-01")
    template = {"name": "t", "version": "1", "page_budget": 2, "sections": [EXPERIENCE_SECTION]}
    result = plan.generate_plan(map_all_direct([exp]), profile_with([exp]), template, "builder")
    assert result["units"][0]["source_ids"] == [exp["id"]]
    assert plan.validate_plan(result, template) == []


def test_positioning_inverts():
    exec_role = entity("experience", organization="BigCo", title="VP Eng", start_date="2019-01-01", positioning=["executive"])
    builder_role = entity("experience", organization="Startup", title="Staff Engineer", start_date="2018-01-01", positioning=["builder"])
    entities = [exec_role, builder_role]
    template = {"name": "t", "version": "1", "page_budget": 2, "sections": [EXPERIENCE_SECTION]}
    mp = map_all_direct(entities)

    builder_plan = plan.generate_plan(mp, profile_with(entities), template, "builder")
    executive_plan = plan.generate_plan(mp, profile_with(entities), template, "executive")

    builder_first = builder_plan["units"][0]["source_ids"][0]
    executive_first = executive_plan["units"][0]["source_ids"][0]
    assert builder_first == builder_role["id"]
    assert executive_first == exec_role["id"]
    # Same facts, only order/emphasis changed.
    assert {u["source_ids"][0] for u in builder_plan["units"]} == {u["source_ids"][0] for u in executive_plan["units"]}


def test_budget_cuts_reported():
    a = entity("experience", organization="A", title="Eng", start_date="2020-01-01")
    b = entity("experience", organization="B", title="Eng", start_date="2019-01-01")
    entities = [a, b]
    template = {"name": "t", "version": "1", "page_budget": 2,
                "sections": [{"id": "experience", "entity_types": ["experience"], "max_items": 1}]}
    result = plan.generate_plan(map_all_direct(entities), profile_with(entities), template, "builder")
    assert len(result["units"]) == 1
    assert len(result["cuts"]) == 1
    assert result["cuts"][0]["entity_id"] in {a["id"], b["id"]}


def test_page_budget_global_cap():
    entities = [entity("experience", organization=f"Org{i}", title="Eng", start_date="2020-01-01") for i in range(5)]
    template = {"name": "t", "version": "1", "page_budget": 1, "units_per_page": 2,
                "sections": [{"id": "experience", "entity_types": ["experience"]}]}
    result = plan.generate_plan(map_all_direct(entities), profile_with(entities), template, "builder")
    assert len(result["units"]) == 2
    assert len(result["cuts"]) == 3


def test_gap_requirement_not_cited():
    exp = entity("experience", organization="Acme", title="Eng", start_date="2020-01-01")
    unused = entity("skill", name="Nuclear")
    mp = [
        {"requirement_id": "req-1", "classification": "direct", "evidence": [{"entity_id": exp["id"], "why": "x"}], "note": ""},
        {"requirement_id": "req-2", "classification": "gap", "evidence": [], "note": ""},
    ]
    template = {"name": "t", "version": "1", "page_budget": 2,
                "sections": [{"id": "experience", "entity_types": ["experience"]},
                             {"id": "skills", "entity_types": ["skill"]}]}
    result = plan.generate_plan(mp, profile_with([exp, unused]), template, "builder")
    cited = {sid for u in result["units"] for sid in u["source_ids"]}
    assert unused["id"] not in cited  # the gap's (absent) evidence never appears
