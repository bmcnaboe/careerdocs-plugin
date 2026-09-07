"""Tests for the structured-Markdown provider."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "skills" / "career-documents" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from careerdocs import ids, schema, util  # noqa: E402
from careerdocs.config import default_config  # noqa: E402
from careerdocs.errors import CareerDocsError, SchemaTooNew  # noqa: E402
from careerdocs.providers import load_provider  # noqa: E402
from careerdocs.providers.base import hash_profile  # noqa: E402
from careerdocs.providers.markdown import MarkdownProvider  # noqa: E402

NOW = util.now()
SRC = ids.new_source_id()


def prov():
    return {"source_id": SRC, "method": "import", "recorded_at": NOW, "actor": "applicant"}


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


def sample_profile():
    contact = common("contact", name="Applicant", headline="Engineer")
    exp = common(
        "experience", organization="Acme", title="Staff Engineer",
        start_date="2019-01-01", end_date="2022-06-01",
        summary="Led a platform team across three product lines.",
    )
    ach = common("achievement", statement="Cut deploy time by 80%.", parent_id=exp["id"])
    exp["achievement_ids"] = [ach["id"]]
    return {
        "schema_version": schema.profile_schema_version(),
        "applicant_ref": "applicant-001",
        "authoritative_provider": "markdown",
        "derived": False,
        "updated_at": NOW,
        "entities": [contact, exp, ach],
        "sources": [
            {"source_id": SRC, "kind": "resume_docx", "location": "sources/r.docx", "captured_at": NOW}
        ],
    }


def make_provider(tmp_path) -> MarkdownProvider:
    return load_provider(tmp_path, default_config())


def test_read_empty_workspace(tmp_path):
    provider = make_provider(tmp_path)
    profile = provider.read()
    assert profile["entities"] == []
    assert profile["derived"] is False


def test_write_then_read_roundtrips(tmp_path):
    provider = make_provider(tmp_path)
    original = sample_profile()
    provider.write(original)
    read_back = provider.read()
    assert hash_profile(read_back) == hash_profile(original)


def test_body_field_stored_as_markdown_body(tmp_path):
    provider = make_provider(tmp_path)
    profile = sample_profile()
    provider.write(profile)
    ach = next(e for e in profile["entities"] if e["type"] == "achievement")
    text = (tmp_path / "profile" / "achievement" / f"{ach['id']}.md").read_text()
    # The statement is in the body, not the JSON frontmatter.
    assert "Cut deploy time by 80%." in text.split("---")[-1]


def test_hash_stable_regardless_of_entity_order(tmp_path):
    provider = make_provider(tmp_path)
    profile = sample_profile()
    h1 = hash_profile(profile)
    reordered = {**profile, "entities": list(reversed(profile["entities"]))}
    assert hash_profile(reordered) == h1


def test_write_removes_retired_entity_files(tmp_path):
    provider = make_provider(tmp_path)
    profile = sample_profile()
    provider.write(profile)
    ach = next(e for e in profile["entities"] if e["type"] == "achievement")
    ach_path = tmp_path / "profile" / "achievement" / f"{ach['id']}.md"
    assert ach_path.exists()
    # Drop the achievement (and its reference) and rewrite.
    kept = [e for e in profile["entities"] if e["type"] != "achievement"]
    for e in kept:
        e.pop("achievement_ids", None)
    provider.write({**profile, "entities": kept})
    assert not ach_path.exists()


def test_sources_ledger(tmp_path):
    provider = make_provider(tmp_path)
    src = {"source_id": ids.new_source_id(), "kind": "note", "location": "n.md", "captured_at": NOW}
    provider.append_source(src)
    provider.append_source(src)  # idempotent by source_id
    assert [s["source_id"] for s in provider.read_sources()] == [src["source_id"]]


def test_approvals_ledger_append_only(tmp_path):
    provider = make_provider(tmp_path)
    provider.append_approval({"diff_id": "diff_1", "diff_hash": "a"})
    provider.append_approval({"diff_id": "diff_1", "diff_hash": "b"})
    assert len(provider.read_approvals()) == 2
    assert provider.find_approval("diff_1")["diff_hash"] == "b"
    assert provider.find_approval("missing") is None


def test_diff_store_and_load(tmp_path):
    provider = make_provider(tmp_path)
    diff = {"diff_id": ids.new_diff_id(), "base_hash": "x", "operations": []}
    provider.store_diff(diff)
    assert provider.load_diff(diff["diff_id"]) == diff
    with pytest.raises(CareerDocsError):
        provider.load_diff("diff_missing")


def test_capabilities(tmp_path):
    caps = make_provider(tmp_path).capabilities()
    assert caps == {"authoritative_ok": True, "search": False, "context": False}


def test_export_produces_derived_copy(tmp_path):
    provider = make_provider(tmp_path)
    provider.write(sample_profile())
    dest = tmp_path / "derived"
    summary = provider.export({"provider": "markdown", "path": str(dest)})
    assert summary["derived"] is True
    copy = MarkdownProvider.at(dest).read()
    assert copy["derived"] is True
    assert len(copy["entities"]) == 3


def test_read_refuses_too_new_schema(tmp_path):
    provider = make_provider(tmp_path)
    profile = sample_profile()
    profile["schema_version"] = "99.0.0"
    provider.write(profile)
    with pytest.raises(SchemaTooNew):
        provider.read()
