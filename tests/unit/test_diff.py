"""Tests for the ProfileDiff engine and the profile subcommands."""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "skills" / "career-documents" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from careerdocs import cli, diff, ids, util  # noqa: E402
from careerdocs.config import default_config  # noqa: E402
from careerdocs.errors import ApprovalMissing, BaseHashMismatch  # noqa: E402
from careerdocs.providers import load_provider  # noqa: E402

NOW = util.now()
SRC = ids.new_source_id()


def prov(method="import"):
    return {"source_id": SRC, "method": method, "recorded_at": NOW, "actor": "applicant"}


def common(entity_type, **extra):
    entity = {
        "id": ids.new_id(entity_type),
        "type": entity_type,
        "visibility": "public",
        "verification": "imported",
        "provenance": [prov()],
        "created_at": NOW,
        "updated_at": NOW,
    }
    entity.update(extra)
    return entity


def add_contact_and_experience():
    contact = common("contact", name="Applicant")
    exp = common("experience", organization="Acme", title="Engineer", start_date="2020-01-01")
    return contact, exp, [
        {"op": "add_entity", "entity": contact},
        {"op": "add_entity", "entity": exp},
    ]


def provider_for(tmp_path, cfg=None):
    return load_provider(tmp_path, cfg or default_config())


def test_make_diff_sets_base_hash_and_summary(tmp_path):
    provider = provider_for(tmp_path)
    _, _, ops = add_contact_and_experience()
    d = diff.make_diff(provider, ops)
    assert d["base_hash"] and d["diff_id"].startswith("diff_")
    assert "Proposed profile changes" in d["summary_md"]
    assert provider.load_diff(d["diff_id"]) == d


def test_diff_hash_is_stable():
    d = {"diff_id": "diff_x", "base_hash": "abc", "operations": [{"op": "retire_entity", "id": "x", "reason": "y"}]}
    assert diff.diff_hash(d) == diff.diff_hash(dict(d))


def test_apply_requires_approval(tmp_path):
    provider = provider_for(tmp_path)
    _, _, ops = add_contact_and_experience()
    d = diff.make_diff(provider, ops)
    with pytest.raises(ApprovalMissing):
        diff.apply(provider, d["diff_id"], cfg=default_config(), workspace=tmp_path)


def test_approve_then_apply(tmp_path):
    provider = provider_for(tmp_path)
    contact, exp, ops = add_contact_and_experience()
    d = diff.make_diff(provider, ops)
    approval = diff.approve(provider, d["diff_id"])
    assert approval["diff_hash"] == diff.diff_hash(d)
    result = diff.apply(provider, d["diff_id"], cfg=default_config(), workspace=tmp_path)
    profile = provider.read()
    assert {e["id"] for e in profile["entities"]} == {contact["id"], exp["id"]}
    assert result["applied"] == d["diff_id"]


def test_apply_refuses_stale_base_hash(tmp_path):
    provider = provider_for(tmp_path)
    _, _, ops = add_contact_and_experience()
    d = diff.make_diff(provider, ops)
    diff.approve(provider, d["diff_id"])
    # Change the profile out from under the diff.
    other = common("skill", name="Python")
    contact = common("contact", name="A")
    provider.write({**provider.read(), "entities": [contact, other]})
    with pytest.raises(BaseHashMismatch):
        diff.apply(provider, d["diff_id"], cfg=default_config(), workspace=tmp_path)


def test_apply_tampered_approval_refused(tmp_path):
    provider = provider_for(tmp_path)
    _, _, ops = add_contact_and_experience()
    d = diff.make_diff(provider, ops)
    provider.append_approval({"diff_id": d["diff_id"], "diff_hash": "wrong", "approved_at": NOW, "by": "x", "scope": "all"})
    with pytest.raises(ApprovalMissing):
        diff.apply(provider, d["diff_id"], cfg=default_config(), workspace=tmp_path)


def test_apply_operations_resolve_conflict():
    contact = common("contact", name="A")
    exp = common("experience", organization="Acme", title="Eng", start_date="2020-01-01")
    exp["conflicts"] = [{
        "field": "end_date",
        "candidates": [
            {"value": "2022-01-01", "provenance": prov()},
            {"value": "2023-01-01", "provenance": prov()},
        ],
    }]
    profile = {
        "schema_version": "1.0.0", "applicant_ref": "a", "authoritative_provider": "markdown",
        "derived": False, "updated_at": NOW, "entities": [contact, exp], "sources": [],
    }
    ops = [{"op": "resolve_conflict", "id": exp["id"], "field": "end_date", "value": "2022-01-01"}]
    updated = diff.apply_operations(profile, ops)
    resolved = next(e for e in updated["entities"] if e["id"] == exp["id"])
    assert resolved["end_date"] == "2022-01-01"
    assert resolved["verification"] == "applicant_verified"
    assert resolved["conflicts"][0]["resolution"]["value"] == "2022-01-01"


def test_apply_operations_retire_and_visibility():
    contact = common("contact", name="A")
    skill = common("skill", name="Python")
    profile = {
        "schema_version": "1.0.0", "applicant_ref": "a", "authoritative_provider": "markdown",
        "derived": False, "updated_at": NOW, "entities": [contact, skill], "sources": [],
    }
    ops = [
        {"op": "set_visibility", "id": skill["id"], "visibility": "private"},
        {"op": "retire_entity", "id": skill["id"], "reason": "duplicate"},
    ]
    updated = diff.apply_operations(profile, ops)
    assert [e["id"] for e in updated["entities"]] == [contact["id"]]


def test_apply_refreshes_derived_export_for_basic_memory(tmp_path):
    cfg = default_config()
    vault = tmp_path / "vault"
    cfg["providers"] = {
        "authoritative": "basic_memory",
        "markdown": {"path": "profile"},
        "basic_memory": {"vault_path": str(vault), "project": "p", "folder": "career"},
    }
    provider = load_provider(tmp_path, cfg)
    _, _, ops = add_contact_and_experience()
    d = diff.make_diff(provider, ops)
    diff.approve(provider, d["diff_id"])
    result = diff.apply(provider, d["diff_id"], cfg=cfg, workspace=tmp_path)
    export_index = tmp_path / "profile" / "profile.md"
    assert export_index.exists()
    assert result["exported"] == [str(tmp_path / "profile")]


# --- CLI ---


def test_cli_diff_approve_apply_validate(tmp_path):
    cli.main(["config", "init", "--workspace", str(tmp_path)])
    _, _, ops = add_contact_and_experience()
    ops_file = tmp_path / "ops.json"
    ops_file.write_text(json.dumps({"operations": ops}), encoding="utf-8")

    assert cli.main(["profile", "diff", str(ops_file), "--workspace", str(tmp_path), "--json"]) == 0
    diff_ids = [p.stem for p in (tmp_path / "profile" / "diffs").glob("*.json")]
    assert len(diff_ids) == 1
    did = diff_ids[0]

    assert cli.main(["profile", "approve", did, "--workspace", str(tmp_path)]) == 0
    assert cli.main(["profile", "apply", did, "--workspace", str(tmp_path)]) == 0
    assert cli.main(["profile", "validate", "--workspace", str(tmp_path)]) == 0
    assert len(load_provider(tmp_path).read()["entities"]) == 2


def test_cli_export_refuses_authoritative(tmp_path):
    cli.main(["config", "init", "--workspace", str(tmp_path)])
    # markdown is authoritative by default; exporting to markdown is refused.
    assert cli.main(["profile", "export", "--to", "markdown", "--workspace", str(tmp_path)]) == 2
