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


CLAUDE_PLUGIN = {"name": "careerdocs", "version": "0.1.0", "description": "Core."}
CODEX_PLUGIN = {**CLAUDE_PLUGIN, "skills": "./skills/"}
CODEX_MARKETPLACE = {
    "name": "careerdocs-plugin",
    "plugins": [{"name": "careerdocs", "source": {"source": "local", "path": "./"}}],
}


def make_repo(tmp_path, skills, *, plugin=True, market=True, codex=True):
    for name, desc in skills.items():
        d = tmp_path / "skills" / name
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text(SKILL.format(name=name, desc=desc), encoding="utf-8")
    cp = tmp_path / ".claude-plugin"
    cp.mkdir()
    if plugin:
        (cp / "plugin.json").write_text(json.dumps(CLAUDE_PLUGIN), encoding="utf-8")
    if market:
        (cp / "marketplace.json").write_text(
            json.dumps({"name": "careerdocs-plugin", "plugins": [
                {"name": "careerdocs", "source": "./", "version": "0.1.0"}]}),
            encoding="utf-8",
        )
    if codex:
        write_codex(tmp_path, CODEX_PLUGIN, CODEX_MARKETPLACE)
    return tmp_path


def write_codex(root, plugin, marketplace):
    (root / ".codex-plugin").mkdir(exist_ok=True)
    (root / ".codex-plugin" / "plugin.json").write_text(json.dumps(plugin), encoding="utf-8")
    (root / ".agents" / "plugins").mkdir(parents=True, exist_ok=True)
    (root / ".agents" / "plugins" / "marketplace.json").write_text(json.dumps(marketplace), encoding="utf-8")


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


def test_codex_matches(tmp_path):
    root = make_repo(tmp_path, {"careerdocs": "Core skill."})
    assert ci.check_codex(root, ci.discover_skills(root)) == []


def test_codex_manifests_are_required(tmp_path):
    root = make_repo(tmp_path, {"careerdocs": "Core."}, codex=False)
    assert any(".codex-plugin/plugin.json is missing" in e for e in ci.check_codex(root, {}))


def test_codex_plugin_must_match_claude_plugin(tmp_path):
    root = make_repo(tmp_path, {"careerdocs": "Core."})
    write_codex(root, {**CODEX_PLUGIN, "version": "9.9.9", "skills": "./other/"}, CODEX_MARKETPLACE)
    errors = ci.check_codex(root, ci.discover_skills(root))
    assert any("version differs" in e for e in errors)
    assert any("./skills/" in e for e in errors)


def test_codex_marketplace_must_point_at_the_root_plugin(tmp_path):
    root = make_repo(tmp_path, {"careerdocs": "Core."})
    write_codex(root, CODEX_PLUGIN, {"name": "other", "plugins": [
        {"name": "careerdocs", "source": {"source": "local", "path": "./plugins/x"}}]})
    errors = ci.check_codex(root, ci.discover_skills(root))
    assert any("name differs" in e for e in errors)
    assert any("exactly one plugin" in e for e in errors)


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
