#!/usr/bin/env python3
"""Package inventory agreement (SC-001).

The Claude package is the repository itself (skills auto-discovered from ``skills/``); the
OpenAI package lists its skills explicitly. This derives the inventory from the ``skills/``
tree and checks it against the Claude manifests (``plugin.json`` / ``marketplace.json`` are
present and internally consistent) and, when it exists, the OpenAI manifest (identical
skill names, descriptions, and paths). It also checks that the package carries no
developer-local configuration, and runs ``claude plugin validate .`` when the Claude CLI
is on PATH. Standard library only; reuses the skills-lint frontmatter parser.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lint_skills  # noqa: E402


def discover_skills(root: Path) -> dict[str, dict]:
    skills_dir = root / "skills"
    skills: dict[str, dict] = {}
    if not skills_dir.is_dir():
        return skills
    for child in sorted(skills_dir.iterdir()):
        skill_md = child / "SKILL.md"
        if not skill_md.is_file():
            continue
        data, _ = lint_skills.parse_frontmatter(skill_md.read_text(encoding="utf-8"))
        metadata = data.get("metadata") if isinstance(data.get("metadata"), dict) else {}
        skills[child.name] = {
            "name": data.get("name"),
            "description": data.get("description"),
            "version": metadata.get("version"),
            "path": f"skills/{child.name}",
        }
    return skills


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def check_claude(root: Path, skills: dict[str, dict]) -> list[str]:
    errors: list[str] = []
    plugin_path = root / ".claude-plugin" / "plugin.json"
    market_path = root / ".claude-plugin" / "marketplace.json"
    if not plugin_path.exists():
        return [".claude-plugin/plugin.json is missing"]
    if not market_path.exists():
        return [".claude-plugin/marketplace.json is missing"]

    plugin = _load_json(plugin_path)
    market = _load_json(market_path)
    plugin_name = plugin.get("name")
    if not plugin_name:
        errors.append("plugin.json has no name")

    entries = [p for p in market.get("plugins", []) if p.get("source") == "./"]
    if len(entries) != 1:
        errors.append(f"marketplace.json must have exactly one plugin with source './', found {len(entries)}")
    else:
        entry = entries[0]
        if entry.get("name") != plugin_name:
            errors.append(f"marketplace plugin name {entry.get('name')!r} != plugin.json name {plugin_name!r}")
        if entry.get("version") != plugin.get("version"):
            errors.append("marketplace plugin version differs from plugin.json version")

    if not skills:
        errors.append("no skills discovered under skills/")
    return errors


def check_openai(root: Path, skills: dict[str, dict]) -> list[str]:
    manifest_path = root / "packages" / "openai" / "manifest.json"
    if not manifest_path.exists():
        return []
    errors: list[str] = []
    manifest = _load_json(manifest_path)
    listed = {s["name"]: s for s in manifest.get("skills", [])}
    if set(listed) != set(skills):
        errors.append(
            f"openai manifest skills {sorted(listed)} != skills tree {sorted(skills)}"
        )
    for name, info in skills.items():
        entry = listed.get(name)
        if entry is None:
            continue
        if entry.get("description") != info["description"]:
            errors.append(f"openai manifest '{name}': description differs from SKILL.md")
        if entry.get("path") != info["path"]:
            errors.append(f"openai manifest '{name}': path {entry.get('path')!r} != {info['path']!r}")
    return errors


# The plugin root is the repository root, so every tracked file is cloned into each
# install. A project-scope MCP config names servers only the maintainer can reach, and
# Claude Code loads a plugin-root ``.mcp.json`` as the plugin's own; declaring an empty
# ``mcpServers`` in plugin.json does not suppress it. Keeping the file untracked is what
# keeps it out of the package.
DEVELOPER_LOCAL = (".mcp.json",)


def check_package_hygiene(root: Path) -> list[str]:
    """Refuse developer-local configuration that the package would ship."""
    if shutil.which("git") is None or not (root / ".git").exists():
        return []
    result = subprocess.run(
        ["git", "ls-files", "--", *DEVELOPER_LOCAL],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return []
    return [
        f"{tracked} is tracked by git, so every install ships it; untrack it and keep it ignored"
        for tracked in sorted(filter(None, result.stdout.splitlines()))
    ]


def claude_validate(root: Path) -> list[str]:
    if shutil.which("claude") is None:
        return []
    result = subprocess.run(
        ["claude", "plugin", "validate", "."],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return [f"`claude plugin validate .` failed:\n{result.stdout}\n{result.stderr}"]
    return []


def run_check(root: Path, *, validate: bool = True) -> list[str]:
    skills = discover_skills(root)
    errors = check_claude(root, skills) + check_openai(root, skills) + check_package_hygiene(root)
    if validate:
        errors += claude_validate(root)
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check package inventory agreement.")
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--no-validate", action="store_true", help="skip `claude plugin validate`")
    args = parser.parse_args(argv)
    errors = run_check(Path(args.root), validate=not args.no_validate)
    for message in errors:
        print(message)
    if errors:
        print(f"package inventory: {len(errors)} problem(s)", file=sys.stderr)
        return 1
    print("package inventory: consistent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
