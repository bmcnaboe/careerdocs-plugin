"""Tests for id generation/parsing and profile validation."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "skills" / "career-documents" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from careerdocs import ids, schema  # noqa: E402
from careerdocs.errors import CareerDocsError, ProfileInvalid  # noqa: E402

import pytest  # noqa: E402

NOW = "2024-01-01T00:00:00Z"
SRC = ids.new_source_id()


def prov(method="import"):
    return {"source_id": SRC, "method": method, "recorded_at": NOW, "actor": "applicant"}


def common(entity_type, **extra):
    entity = {
        "id": ids.new_id(entity_type),
        "type": entity_type,
        "visibility": "public",
        "verification": "applicant_verified",
        "provenance": [prov()],
        "created_at": NOW,
        "updated_at": NOW,
    }
    entity.update(extra)
    return entity


def make_profile(entities):
    return {
        "schema_version": schema.profile_schema_version(),
        "applicant_ref": "applicant-001",
        "authoritative_provider": "markdown",
        "derived": False,
        "updated_at": NOW,
        "entities": entities,
        "sources": [
            {"source_id": SRC, "kind": "resume_docx", "location": "sources/r.docx", "captured_at": NOW}
        ],
    }


# --- ids ---


def test_new_ulid_matches_pattern():
    assert ids.is_valid_ulid(ids.new_ulid())


def test_new_id_and_parse_roundtrip():
    ident = ids.new_id("experience")
    prefix, ulid = ids.parse_id(ident)
    assert prefix == "experience" and ids.is_valid_ulid(ulid)


def test_new_id_rejects_unknown_type():
    with pytest.raises(CareerDocsError):
        ids.new_id("nonsense")


def test_parse_id_rejects_bad_ulid():
    with pytest.raises(CareerDocsError):
        ids.parse_id("experience_toolittle")


def test_source_and_diff_ids():
    assert ids.parse_id(ids.new_source_id())[0] == "src"
    assert ids.parse_id(ids.new_diff_id())[0] == "diff"


def test_ulids_are_unique():
    assert len({ids.new_ulid() for _ in range(1000)}) == 1000


# --- profile validation ---


def test_minimal_valid_profile():
    contact = common("contact", name="Applicant")
    assert schema.validate_profile(make_profile([contact])) == []


def test_empty_profile_is_valid():
    assert schema.validate_profile(make_profile([])) == []


def test_more_than_one_contact_fails():
    profile = make_profile([common("contact", name="A"), common("contact", name="B")])
    assert any("more than one contact" in e for e in schema.validate_profile(profile))


def test_entities_without_contact_fails():
    exp = common("experience", organization="Acme", title="Engineer", start_date="2020-01-01")
    assert any("no contact" in e for e in schema.validate_profile(make_profile([exp])))


def test_future_date_fails():
    contact = common("contact", name="A")
    exp = common("experience", organization="Acme", title="Eng", start_date="2999-01-01")
    errors = schema.validate_profile(make_profile([contact, exp]))
    assert any("in the future" in e for e in errors)


def test_end_before_start_fails():
    contact = common("contact", name="A")
    exp = common(
        "experience", organization="Acme", title="Eng",
        start_date="2020-05-01", end_date="2019-01-01",
    )
    errors = schema.validate_profile(make_profile([contact, exp]))
    assert any("before start_date" in e for e in errors)


def test_unresolved_reference_fails():
    contact = common("contact", name="A")
    exp = common(
        "experience", organization="Acme", title="Eng",
        start_date="2020-01-01", achievement_ids=[ids.new_id("achievement")],
    )
    errors = schema.validate_profile(make_profile([contact, exp]))
    assert any("does not resolve" in e for e in errors)


def test_achievement_parent_must_be_experience_or_project():
    contact = common("contact", name="A")
    skill = common("skill", name="Python")
    ach = common("achievement", statement="Did a thing", parent_id=skill["id"])
    errors = schema.validate_profile(make_profile([contact, skill, ach]))
    assert any("experience or project" in e for e in errors)


def test_resolved_references_pass():
    contact = common("contact", name="A")
    exp = common("experience", organization="Acme", title="Eng", start_date="2020-01-01")
    ach = common("achievement", statement="Shipped it", parent_id=exp["id"])
    exp["achievement_ids"] = [ach["id"]]
    assert schema.validate_profile(make_profile([contact, exp, ach])) == []


def test_unresolved_conflict_fields():
    exp = common("experience", organization="Acme", title="Eng", start_date="2020-01-01")
    exp["conflicts"] = [
        {"field": "end_date", "candidates": [
            {"value": "2022-01-01", "provenance": prov()},
            {"value": "2023-01-01", "provenance": prov()},
        ]},
        {"field": "title", "candidates": [
            {"value": "Eng", "provenance": prov()},
            {"value": "Senior Eng", "provenance": prov()},
        ], "resolution": {"value": "Senior Eng", "resolved_at": NOW, "by": "applicant"}},
    ]
    assert schema.unresolved_conflict_fields(exp) == {"end_date"}


def test_assert_valid_raises():
    with pytest.raises(ProfileInvalid):
        schema.assert_valid_profile(make_profile([common("contact"), common("contact")]))


def test_schema_version_is_semver():
    assert schema.profile_schema_version().count(".") == 2
