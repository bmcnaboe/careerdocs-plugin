"""Tests for the Basic Memory provider."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "skills" / "career-documents" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from careerdocs import ids, schema, util  # noqa: E402
from careerdocs.config import default_config  # noqa: E402
from careerdocs.providers import load_provider  # noqa: E402
from careerdocs.providers.base import hash_profile  # noqa: E402
from careerdocs.providers.basic_memory import BasicMemoryProvider, entity_title  # noqa: E402
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
    contact = common("contact", name="Applicant")
    skill = common("skill", name="Python", level="expert")
    exp = common(
        "experience", organization="Acme", title="Staff Engineer",
        start_date="2019-01-01", summary="Led a platform team.", skill_ids=[skill["id"]],
    )
    ach = common("achievement", statement="Cut deploy time by 80%.", parent_id=exp["id"])
    exp["achievement_ids"] = [ach["id"]]
    return {
        "schema_version": schema.profile_schema_version(),
        "applicant_ref": "applicant-001",
        "authoritative_provider": "basic_memory",
        "derived": False,
        "updated_at": NOW,
        "entities": [contact, skill, exp, ach],
        "sources": [
            {"source_id": SRC, "kind": "resume_docx", "location": "sources/r.docx", "captured_at": NOW}
        ],
    }


def bm_config(vault):
    cfg = default_config()
    cfg["providers"] = {
        "authoritative": "basic_memory",
        "basic_memory": {"vault_path": str(vault), "project": "test-vault", "folder": "career"},
    }
    return cfg


def test_load_provider_selects_basic_memory(tmp_path):
    provider = load_provider(tmp_path, bm_config(tmp_path / "vault"))
    assert isinstance(provider, BasicMemoryProvider)


def test_write_then_read_roundtrips(tmp_path):
    provider = load_provider(tmp_path, bm_config(tmp_path / "vault"))
    original = sample_profile()
    provider.write(original)
    assert hash_profile(provider.read()) == hash_profile(original)


def test_note_format(tmp_path):
    vault = tmp_path / "vault"
    provider = load_provider(tmp_path, bm_config(vault))
    profile = sample_profile()
    provider.write(profile)
    ach = next(e for e in profile["entities"] if e["type"] == "achievement")
    note = (vault / "career" / "achievement" / f"{ach['id']}.md").read_text()
    assert '"permalink": "career/achievement/' in note
    assert "## Observations" in note
    assert f"#{ach['id']}" in note
    assert "## Relations" in note
    assert "- part_of [[Staff Engineer]]" in note


def test_experience_note_has_evidences_relation(tmp_path):
    vault = tmp_path / "vault"
    provider = load_provider(tmp_path, bm_config(vault))
    profile = sample_profile()
    provider.write(profile)
    exp = next(e for e in profile["entities"] if e["type"] == "experience")
    note = (vault / "career" / "experience" / f"{exp['id']}.md").read_text()
    assert "- evidences [[Python]]" in note


def test_permalinks_use_folder(tmp_path):
    vault = tmp_path / "vault"
    provider = load_provider(tmp_path, bm_config(vault))
    profile = sample_profile()
    provider.write(profile)
    read_back = {e["id"] for e in provider.read()["entities"]}
    assert read_back == {e["id"] for e in profile["entities"]}


def test_capabilities_report_search_and_context(tmp_path):
    provider = load_provider(tmp_path, bm_config(tmp_path / "vault"))
    assert provider.capabilities() == {"authoritative_ok": True, "search": True, "context": True}


def test_export_to_markdown_is_derived(tmp_path):
    vault = tmp_path / "vault"
    provider = load_provider(tmp_path, bm_config(vault))
    profile = sample_profile()
    provider.write(profile)
    dest = tmp_path / "profile-export"
    summary = provider.export({"provider": "markdown", "path": str(dest)})
    assert summary["derived"] is True
    exported = MarkdownProvider.at(dest).read()
    assert exported["derived"] is True
    assert {e["id"] for e in exported["entities"]} == {e["id"] for e in profile["entities"]}


def test_entity_title_labels():
    exp = common("experience", organization="Acme", title="Engineer", start_date="2020-01-01")
    assert entity_title(exp) == "Engineer"
    skill = common("skill", name="Rust")
    assert entity_title(skill) == "Rust"
