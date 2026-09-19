"""Tests for visibility filtering and per-document approvals."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "skills" / "careerdocs" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from careerdocs import ids, schema, util, visibility  # noqa: E402
from careerdocs.config import default_config  # noqa: E402
from careerdocs.providers import load_provider  # noqa: E402

NOW = util.now()
SRC = ids.new_source_id()


def prov():
    return {"source_id": SRC, "method": "import", "recorded_at": NOW, "actor": "a"}


def common(entity_type, **extra):
    e = {
        "id": ids.new_id(entity_type), "type": entity_type, "visibility": "public",
        "verification": "applicant_verified", "provenance": [prov()],
        "created_at": NOW, "updated_at": NOW,
    }
    e.update(extra)
    return e


def profile_with(entities):
    return {
        "schema_version": schema.profile_schema_version(), "applicant_ref": "a",
        "authoritative_provider": "markdown", "derived": False, "updated_at": NOW,
        "entities": entities, "sources": [
            {"source_id": SRC, "kind": "note", "location": "n.md", "captured_at": NOW}],
    }


def test_is_visible_rules():
    public = common("skill", name="A")
    private = common("skill", name="B", visibility="private")
    restricted = common("skill", name="C", visibility="restricted")
    unverified = common("skill", name="D", verification="unverified")

    assert visibility.is_visible(public)
    assert not visibility.is_visible(private)
    assert not visibility.is_visible(unverified)
    assert not visibility.is_visible(restricted)  # no document approval
    assert visibility.is_visible(restricted, document="resume.docx", approved_docs={"resume.docx"})


def test_filter_removes_private_and_cleans_references():
    contact = common("contact", name="Jordan")
    exp = common("experience", organization="Acme", title="Eng", start_date="2020-01-01")
    private_ach = common("achievement", statement="secret", parent_id=exp["id"], visibility="private")
    exp["achievement_ids"] = [private_ach["id"]]
    filtered = visibility.filter_visible(profile_with([contact, exp, private_ach]))
    ids_kept = {e["id"] for e in filtered["entities"]}
    assert private_ach["id"] not in ids_kept
    kept_exp = next(e for e in filtered["entities"] if e["id"] == exp["id"])
    assert kept_exp["achievement_ids"] == []
    assert schema.validate_profile(filtered) == []


def test_cascade_drops_achievement_when_parent_private():
    contact = common("contact", name="Jordan")
    private_exp = common("experience", organization="Acme", title="Eng", start_date="2020-01-01", visibility="private")
    ach = common("achievement", statement="did a thing", parent_id=private_exp["id"])
    filtered = visibility.filter_visible(profile_with([contact, private_exp, ach]))
    ids_kept = {e["id"] for e in filtered["entities"]}
    assert private_exp["id"] not in ids_kept
    assert ach["id"] not in ids_kept  # cascaded out
    assert schema.validate_profile(filtered) == []


def test_approved_documents_from_approvals():
    approvals = [
        {"diff_id": "d1", "diff_hash": "x"},
        {"diff_id": "d2", "diff_hash": "y", "document": "outputs/resume.docx"},
    ]
    assert visibility.approved_documents(approvals) == {"outputs/resume.docx"}


def test_approve_document_recorded(tmp_path):
    from careerdocs import diff

    provider = load_provider(tmp_path, default_config())
    contact = common("contact", name="Jordan")
    d = diff.make_diff(provider, [{"op": "add_entity", "entity": contact}])
    diff.approve(provider, d["diff_id"], document="outputs/resume.docx")
    assert visibility.approved_documents(provider.read_approvals()) == {"outputs/resume.docx"}
