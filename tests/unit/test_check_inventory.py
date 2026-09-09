"""Tests for the package inventory check."""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import check_inventory as ci  # noqa: E402

SKILL = """\
---
name: {name}
description: {desc}
license: MIT
metadata:
  version: "0.1.0"
  author: "x"
---

body
"""


def make_repo(tmp_path, skills, *, plugin=True, market=True, openai=None):
    for name, desc in skills.items():
        d = tmp_path / "skills" / name
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text(SKILL.format(name=name, desc=desc), encoding="utf-8")
    cp = tmp_path / ".claude-plugin"
    cp.mkdir()
    if plugin:
        (cp / "plugin.json").write_text(json.dumps({"name": "careerdocs", "version": "0.1.0"}), encoding="utf-8")
    if market:
        (cp / "marketplace.json").write_text(
            json.dumps({"name": "careerdocs-plugin", "plugins": [
                {"name": "careerdocs", "source": "./", "version": "0.1.0"}]}),
            encoding="utf-8",
        )
    if openai is not None:
        p = tmp_path / "packages" / "openai"
        p.mkdir(parents=True)
        (p / "manifest.json").write_text(json.dumps(openai), encoding="utf-8")
    return tmp_path


def test_discover_skills(tmp_path):
    make_repo(tmp_path, {"careerdocs": "Core skill."})
    skills = ci.discover_skills(tmp_path)
    assert skills["careerdocs"]["version"] == "0.1.0"
    assert skills["careerdocs"]["path"] == "skills/careerdocs"


def test_claude_ok(tmp_path):
    make_repo(tmp_path, {"careerdocs": "Core skill."})
    assert ci.check_claude(tmp_path, ci.discover_skills(tmp_path)) == []


def test_claude_missing_plugin(tmp_path):
    make_repo(tmp_path, {"careerdocs": "Core."}, plugin=False)
    assert any("plugin.json is missing" in e for e in ci.check_claude(tmp_path, {}))


def test_marketplace_name_mismatch(tmp_path):
    root = make_repo(tmp_path, {"careerdocs": "Core."})
    (root / ".claude-plugin" / "marketplace.json").write_text(
        json.dumps({"name": "x", "plugins": [{"name": "other", "source": "./", "version": "0.1.0"}]}),
        encoding="utf-8",
    )
    assert any("name" in e for e in ci.check_claude(root, ci.discover_skills(root)))


def test_openai_absent_is_skipped(tmp_path):
    make_repo(tmp_path, {"careerdocs": "Core."})
    assert ci.check_openai(tmp_path, ci.discover_skills(tmp_path)) == []


def test_openai_matches(tmp_path):
    root = make_repo(
        tmp_path, {"careerdocs": "Core skill."},
        openai={"name": "careerdocs", "version": "0.1.0", "skills": [
            {"name": "careerdocs", "description": "Core skill.", "path": "skills/careerdocs"}]},
    )
    assert ci.check_openai(root, ci.discover_skills(root)) == []


def test_openai_description_mismatch(tmp_path):
    root = make_repo(
        tmp_path, {"careerdocs": "Core skill."},
        openai={"name": "careerdocs", "version": "0.1.0", "skills": [
            {"name": "careerdocs", "description": "WRONG", "path": "skills/careerdocs"}]},
    )
    assert any("description differs" in e for e in ci.check_openai(root, ci.discover_skills(root)))


def test_openai_missing_skill(tmp_path):
    root = make_repo(
        tmp_path, {"careerdocs": "Core.", "onboard": "Onboard."},
        openai={"name": "careerdocs", "version": "0.1.0", "skills": [
            {"name": "careerdocs", "description": "Core.", "path": "skills/careerdocs"}]},
    )
    assert any("!= skills tree" in e for e in ci.check_openai(root, ci.discover_skills(root)))


def test_package_hygiene_ignores_a_non_git_tree(tmp_path):
    make_repo(tmp_path, {"careerdocs": "Core."})
    (tmp_path / ".mcp.json").write_text("{}", encoding="utf-8")
    assert ci.check_package_hygiene(tmp_path) == []


def test_package_hygiene_flags_a_tracked_mcp_config(tmp_path):
    root = make_repo(tmp_path, {"careerdocs": "Core."})
    (root / ".mcp.json").write_text("{}", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "add", ".mcp.json"], cwd=root, check=True)
    errors = ci.check_package_hygiene(root)
    assert len(errors) == 1 and ".mcp.json is tracked by git" in errors[0]


def test_package_hygiene_passes_when_the_mcp_config_is_untracked(tmp_path):
    root = make_repo(tmp_path, {"careerdocs": "Core."})
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    (root / ".mcp.json").write_text("{}", encoding="utf-8")
    assert ci.check_package_hygiene(root) == []


def test_repo_inventory_consistent():
    # The real repo passes (claude validate included when the CLI is present).
    assert ci.run_check(ROOT) == []
