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


def empty_profile():
    return {
        "schema_version": schema.profile_schema_version(),
        "applicant_ref": "applicant", "authoritative_provider": "markdown",
        "derived": False, "updated_at": "2024-01-01T00:00:00Z", "entities": [], "sources": [],
    }


def experiences(ops):
    return [op["entity"] for op in ops if op["op"] == "add_entity" and op["entity"]["type"] == "experience"]


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
    ops = merge.build_operations(provider.read(), CANDIDATES)
    d = diff.make_diff(provider, ops)
    diff.approve(provider, d["diff_id"])
    diff.apply(provider, d["diff_id"], cfg=default_config(), workspace=tmp_path)
    profile = provider.read()
    globex = next(e for e in profile["entities"] if e.get("organization") == "Globex Corporation")
    assert len(globex["conflicts"]) == 1
    assert schema.validate_profile(profile) == []


def test_deduplicates_against_existing_profile(tmp_path):
    # Re-merging the same candidates against a profile that already has them
    # produces update operations, not duplicate adds.
    provider = load_provider(tmp_path, default_config())
    ops = merge.build_operations(provider.read(), CANDIDATES)
    d = diff.make_diff(provider, ops)
    diff.approve(provider, d["diff_id"])
    diff.apply(provider, d["diff_id"], cfg=default_config(), workspace=tmp_path)
    again = merge.build_operations(provider.read(), CANDIDATES)
    assert all(op["op"] != "add_entity" for op in again if op["op"] == "add_entity" and op["entity"]["type"] == "experience")
