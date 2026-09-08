"""Tests for the version-agreement check."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import check_versions as cv  # noqa: E402

PYPROJECT = '[project]\nname = "careerdocs-plugin"\nversion = "0.1.0"\n'

SKILL = """\
---
name: {name}
description: ok
license: MIT
metadata:
  version: "{version}"
  author: "x"
---

body
"""


def make_repo(tmp_path, *, skills=None, manifests=None):
    (tmp_path / "pyproject.toml").write_text(PYPROJECT, encoding="utf-8")
    for name, version in (skills or {}).items():
        d = tmp_path / "skills" / name
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text(SKILL.format(name=name, version=version), encoding="utf-8")
    for rel, content in (manifests or {}).items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(content), encoding="utf-8")
    return tmp_path


def test_version_of_record(tmp_path):
    make_repo(tmp_path)
    assert cv.version_of_record(tmp_path) == "0.1.0"


def test_matching_skill_passes(tmp_path):
    make_repo(tmp_path, skills={"careerdocs": "0.1.0"})
    _, errors, _ = cv.run_check(tmp_path)
    assert errors == []


def test_mismatched_skill_fails(tmp_path):
    make_repo(tmp_path, skills={"careerdocs": "0.2.0"})
    _, errors, _ = cv.run_check(tmp_path)
    assert any("careerdocs" in e and "0.2.0" in e for e in errors)


def test_absent_manifests_reported(tmp_path):
    make_repo(tmp_path)
    _, _, absent = cv.run_check(tmp_path)
    assert set(absent) == {"plugin.json", "marketplace.json", "openai manifest.json"}


def test_plugin_manifest_version_checked(tmp_path):
    make_repo(tmp_path, manifests={".claude-plugin/plugin.json": {"version": "9.9.9"}})
    _, errors, absent = cv.run_check(tmp_path)
    assert any("plugin.json" in e and "9.9.9" in e for e in errors)
    assert "plugin.json" not in absent


def test_marketplace_plugin_entries_checked(tmp_path):
    make_repo(
        tmp_path,
        manifests={".claude-plugin/marketplace.json": {"plugins": [{"version": "0.0.1"}]}},
    )
    _, errors, _ = cv.run_check(tmp_path)
    assert any("plugins[0]" in e for e in errors)


def test_all_agree(tmp_path):
    make_repo(
        tmp_path,
        skills={"careerdocs": "0.1.0", "career-onboard": "0.1.0"},
        manifests={
            ".claude-plugin/plugin.json": {"version": "0.1.0"},
            ".claude-plugin/marketplace.json": {"plugins": [{"version": "0.1.0"}]},
            "packages/openai/manifest.json": {"version": "0.1.0"},
        },
    )
    _, errors, absent = cv.run_check(tmp_path)
    assert errors == [] and absent == []


def test_require_manifests_fails_when_absent(tmp_path):
    make_repo(tmp_path)
    _, errors, _ = cv.run_check(tmp_path, require_manifests=True)
    assert any("required manifest absent" in e for e in errors)


def test_repo_versions_agree():
    # The real repo agrees and now carries every required manifest.
    _, errors, absent = cv.run_check(ROOT, require_manifests=True)
    assert errors == []
    assert absent == []
