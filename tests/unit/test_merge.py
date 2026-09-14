"""Tests for candidate merging into ProfileDiff operations."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "skills" / "careerdocs" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from careerdocs import diff, merge, schema  # noqa: E402
from careerdocs.config import default_config  # noqa: E402
from careerdocs.providers import load_provider  # noqa: E402

CANDIDATES = json.loads((ROOT / "tests" / "fixtures" / "candidates.json").read_text())

# An applicant statement adding one achievement under the Globex role the fixture already
# holds; the role candidate is only there so the achievement's parent_ref resolves.
STATEMENT = {
    "source_id": "src_CCCCCCCCCCCCCCCCCCCCCCCCCC", "method": "statement", "recorded_at": "2024-06-01T00:00:00Z",
    "actor": "applicant", "excerpt": "At Globex I also launched the incident-response program.",
}
NEW_ACHIEVEMENT = {
    "candidates": [
        {
            "type": "experience", "ref": "globex", "provenance": STATEMENT,
            "organization": "Globex Corporation", "title": "Engineering Manager", "start_date": "2018-03",
        },
        {
            "type": "achievement", "parent_ref": "globex", "provenance": STATEMENT,
            "statement": "Launched the company-wide incident-response program.",
        },
    ]
}


def empty_profile():
    return {
        "schema_version": schema.profile_schema_version(),
        "applicant_ref": "applicant", "authoritative_provider": "markdown",
        "derived": False, "updated_at": "2024-01-01T00:00:00Z", "entities": [], "sources": [],
    }


def experiences(ops):
    return [op["entity"] for op in ops if op["op"] == "add_entity" and op["entity"]["type"] == "experience"]


def apply_ops(provider, ops, workspace):
    d = diff.make_diff(provider, ops)
    diff.approve(provider, d["diff_id"])
    diff.apply(provider, d["diff_id"], cfg=default_config(), workspace=workspace)
    return d


def test_disagreeing_resumes_yield_one_experience_with_conflict():
    ops = merge.build_operations(empty_profile(), CANDIDATES)
    globex = [e for e in experiences(ops) if e["organization"] == "Globex Corporation"]
    assert len(globex) == 1
    entity = globex[0]
    # Both sources' provenance survive.
    assert len(entity["provenance"]) == 2
    # Exactly one conflict, on the end date.
    assert len(entity["conflicts"]) == 1
    assert entity["conflicts"][0]["field"] == "end_date"
    values = {c["value"] for c in entity["conflicts"][0]["candidates"]}
    assert values == {"2021-06", "2021-08"}


def test_precedence_picks_newest_import_as_winner():
    ops = merge.build_operations(empty_profile(), CANDIDATES)
    globex = next(e for e in experiences(ops) if e["organization"] == "Globex Corporation")
    # B (recorded later) wins the end_date.
    assert globex["end_date"] == "2021-08"


def test_initech_is_separate_experience():
    ops = merge.build_operations(empty_profile(), CANDIDATES)
    orgs = {e["organization"] for e in experiences(ops)}
    assert orgs == {"Globex Corporation", "Initech"}


def test_achievements_link_to_globex():
    ops = merge.build_operations(empty_profile(), CANDIDATES)
    globex = next(e for e in experiences(ops) if e["organization"] == "Globex Corporation")
    achievements = [op["entity"] for op in ops if op["op"] == "add_entity" and op["entity"]["type"] == "achievement"]
    assert len(achievements) == 2
    assert set(globex["achievement_ids"]) == {a["id"] for a in achievements}
    for ach in achievements:
        assert ach["parent_id"] == globex["id"]


def test_skills_and_education_present():
    ops = merge.build_operations(empty_profile(), CANDIDATES)
    types = [op["entity"]["type"] for op in ops if op["op"] == "add_entity"]
    assert types.count("skill") == 4
    assert types.count("education") == 1
    assert types.count("contact") == 1


def test_merged_diff_applies_cleanly(tmp_path):
    provider = load_provider(tmp_path, default_config())
    apply_ops(provider, merge.build_operations(provider.read(), CANDIDATES), tmp_path)
    profile = provider.read()
    globex = next(e for e in profile["entities"] if e.get("organization") == "Globex Corporation")
    assert len(globex["conflicts"]) == 1
    assert schema.validate_profile(profile) == []


def test_deduplicates_against_existing_profile(tmp_path):
    # Re-merging the same candidates against a profile that already has them
    # produces update operations, not duplicate adds.
    provider = load_provider(tmp_path, default_config())
    apply_ops(provider, merge.build_operations(provider.read(), CANDIDATES), tmp_path)
    again = merge.build_operations(provider.read(), CANDIDATES)
    assert all(op["op"] != "add_entity" for op in again if op["op"] == "add_entity" and op["entity"]["type"] == "experience")


def test_achievement_on_existing_parent_links_both_directions(tmp_path):
    provider = load_provider(tmp_path, default_config())
    apply_ops(provider, merge.build_operations(provider.read(), CANDIDATES), tmp_path)
    before = provider.read()
    globex = next(e for e in before["entities"] if e.get("organization") == "Globex Corporation")

    ops = merge.build_operations(before, NEW_ACHIEVEMENT)
    added = [op["entity"] for op in ops if op["op"] == "add_entity"]
    assert [e["type"] for e in added] == ["achievement"]  # the existing role is not re-added
    achievement = added[0]
    assert achievement["parent_id"] == globex["id"]
    links = [op for op in ops if op["op"] == "update_field" and op["field"] == "achievement_ids"]
    assert links == [{
        "op": "update_field", "id": globex["id"], "field": "achievement_ids",
        "from": globex["achievement_ids"], "to": globex["achievement_ids"] + [achievement["id"]],
        "provenance": STATEMENT,
    }]

    d = apply_ops(provider, ops, tmp_path)
    assert f"{globex['id']} `achievement_ids`" in d["summary_md"]
    after = provider.read()
    linked = next(e for e in after["entities"] if e["id"] == globex["id"])
    assert linked["achievement_ids"] == globex["achievement_ids"] + [achievement["id"]]
    assert schema.validate_profile(after) == []
