"""Tests for the content plan builder."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "skills" / "careerdocs" / "scripts"
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


COVER_TEMPLATE = {
    "name": "letter", "kind": "cover_letter", "version": "1", "page_budget": 1, "units_per_page": 6,
    "sections": [
        {"id": "header", "placeholder": "contact", "entity_types": ["contact"], "max_items": 1},
        {"id": "body", "kind": "sentence", "entity_types": ["experience", "achievement", "skill"], "max_items": 6},
    ],
}


def test_cover_letter_units_are_sentences():
    exp = entity("experience", organization="Acme", title="Eng", start_date="2020-01-01")
    result = plan.generate_plan(map_all_direct([exp]), profile_with([exp]), COVER_TEMPLATE, "builder")
    body = [u for u in result["units"] if u["section_id"] == "body"]
    assert body and all(u["kind"] == "sentence" for u in body)
    assert result["kind"] == "cover_letter"


def test_cover_letter_orders_by_requirement_value():
    high = entity("experience", organization="High", title="Eng", start_date="2020-01-01")
    low = entity("experience", organization="Low", title="Eng", start_date="2019-01-01")
    mapping = [
        {"requirement_id": "req-1", "classification": "direct", "evidence": [{"entity_id": high["id"], "why": "x"}], "note": ""},
        {"requirement_id": "req-2", "classification": "transferable", "evidence": [{"entity_id": low["id"], "why": "x"}], "note": ""},
    ]
    brief = {"requirements": [{"id": "req-1", "kind": "must"}, {"id": "req-2", "kind": "nice"}], "recommended_positioning": "builder"}
    result = plan.generate_plan(mapping, profile_with([high, low]), COVER_TEMPLATE, "builder", brief=brief)
    body = [u for u in result["units"] if u["section_id"] == "body"]
    assert body[0]["source_ids"][0] == high["id"]


def test_cover_letter_page_budget_cuts():
    entities = [entity("achievement", statement=f"Did thing {i}", parent_id="x") for i in range(10)]
    # achievements need a parent to render; use a fake parent id but they are still cited.
    mapping = map_all_direct(entities)
    template = {**COVER_TEMPLATE, "sections": [
        {"id": "body", "kind": "sentence", "entity_types": ["achievement"], "max_items": 20}]}
    result = plan.generate_plan(mapping, profile_with(entities), template, "builder")
    # page_budget 1 * units_per_page 6 = cap 6.
    assert len(result["units"]) == 6
    assert len(result["cuts"]) == 4


def test_baseline_selects_all_visible():
    contact = entity("contact", name="A")
    exp = entity("experience", organization="Acme", title="Eng", start_date="2020-01-01")
    private_skill = entity("skill", name="Secret", visibility="private")
    public_skill = entity("skill", name="Python")
    entities = [contact, exp, private_skill, public_skill]
    template = {"name": "t", "version": "1", "page_budget": 2, "sections": [
        {"id": "header", "entity_types": ["contact"]},
        {"id": "experience", "entity_types": ["experience"]},
        {"id": "skills", "entity_types": ["skill"]},
    ]}
    # No map at all: baseline includes every visible entity, excludes private.
    result = plan.generate_plan([], profile_with(entities), template, "builder", baseline=True)
    ids = {sid for u in result["units"] for sid in u["source_ids"]}
    assert exp["id"] in ids and public_skill["id"] in ids and contact["id"] in ids
    assert private_skill["id"] not in ids


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


# --- unit text conventions and chronology ---

RESUME_SECTION = {"id": "experience", "entity_types": ["experience", "achievement"], "max_items": 20}


def test_contact_unit_is_name_then_details():
    contact = entity("contact", name="A B", email="a@example.com", phone="(555) 555-0100",
                     location="Metropolis, USA", links=[{"label": "GitHub", "url": "https://github.com/ab/"}])
    assert plan._entity_text(contact) == "A B\nMetropolis, USA · (555) 555-0100 · a@example.com · github.com/ab"
    assert plan.display_link("https://www.linkedin.com/in/handle/") == "linkedin.com/in/handle"


def test_experience_unit_separates_role_and_dates_with_a_tab():
    exp = entity("experience", organization="Acme", title="Eng", start_date="2018-03", end_date="2021-06-15")
    assert plan._entity_text(exp) == "Eng, Acme\tMar 2018 – Jun 2021"
    current = entity("experience", organization="Acme", title="Eng", start_date="2022")
    assert plan._entity_text(current) == "Eng, Acme\t2022 – present"


def test_experience_section_is_reverse_chronological_with_achievements_under_their_role():
    old = entity("experience", organization="Old", title="Eng", start_date="2015-01", positioning=["builder"])
    new = entity("experience", organization="New", title="Lead", start_date="2020-01", positioning=["executive"])
    old_win = entity("achievement", statement="Did old thing", parent_id=old["id"], positioning=["builder"])
    new_win = entity("achievement", statement="Did new thing", parent_id=new["id"])
    project = entity("project", name="Side", organization="New")
    project_win = entity("achievement", statement="Shipped side", parent_id=project["id"], positioning=["builder"])
    entities = [old, new, old_win, new_win, project, project_win]
    template = {"name": "t", "version": "1", "page_budget": 2, "sections": [RESUME_SECTION]}
    result = plan.generate_plan(map_all_direct(entities), profile_with(entities), template, "builder")
    order = [u["source_ids"][0] for u in result["units"]]
    # Newest role first despite builder positioning; each role's achievements follow it in
    # emphasis order, and a project achievement sits under the role at its organization.
    assert order == [new["id"], project_win["id"], new_win["id"], old["id"], old_win["id"]]
    assert [u["unit_id"] for u in result["units"]] == ["u1", "u2", "u3", "u4", "u5"]


def test_page_cap_never_cuts_the_contact_or_a_role_with_achievements():
    contact = entity("contact", name="A B", email="a@example.com")
    role = entity("experience", organization="Acme", title="Eng", start_date="2020-01")
    wins = [entity("achievement", statement=f"Win {i}", parent_id=role["id"], positioning=["builder"]) for i in range(4)]
    entities = [contact, role, *wins]
    template = {"name": "t", "version": "1", "page_budget": 1, "units_per_page": 4, "sections": [
        {"id": "header", "entity_types": ["contact"], "max_items": 1}, RESUME_SECTION]}
    result = plan.generate_plan(map_all_direct(entities), profile_with(entities), template, "builder")
    kept = [u["source_ids"][0] for u in result["units"]]
    assert len(kept) == 4 and contact["id"] in kept and role["id"] in kept
    assert len(result["cuts"]) == 2


def test_role_summary_is_a_second_line_only_when_the_section_opts_in():
    exp = entity("experience", organization="Acme", title="Eng", start_date="2018-03", summary="A fintech startup.")
    assert plan._entity_text(exp, {"id": "experience", "entity_types": ["experience"]}) == "Eng, Acme\tMar 2018 – present"
    with_summary = plan._entity_text(exp, {"id": "experience", "entity_types": ["experience"], "role_summaries": True})
    assert with_summary == "Eng, Acme\tMar 2018 – present\nA fintech startup."


def test_page_budget_override_caps_the_plan():
    entities = [entity("experience", organization=f"Org{i}", title="Eng", start_date="2020-01") for i in range(5)]
    template = {"name": "t", "version": "1", "page_budget": 2, "units_per_page": 2,
                "sections": [{"id": "experience", "entity_types": ["experience"]}]}
    result = plan.generate_plan(map_all_direct(entities), profile_with(entities), template, "builder", page_budget=1)
    assert result["page_budget"] == 1 and len(result["units"]) == 2 and len(result["cuts"]) == 3
