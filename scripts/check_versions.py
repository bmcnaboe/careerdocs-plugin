#!/usr/bin/env python3
"""One version everywhere.

``pyproject.toml`` holds the version of record. Every ``skills/*/SKILL.md`` must declare
``metadata.version`` equal to it, and every package manifest that carries a version
(``.claude-plugin/plugin.json``, ``.claude-plugin/marketplace.json``, and
``.codex-plugin/plugin.json``) must agree, as must the CLI's own ``__version__``. A missing manifest is reported as absent and,
unless ``--allow-absent-manifests`` is passed, fails the check.

Standard library only; reuses the skills-lint frontmatter parser.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lint_skills  # noqa: E402

PACKAGE_INIT = Path("skills/careerdocs/scripts/careerdocs/__init__.py")

MANIFESTS = {
    "plugin.json": Path(".claude-plugin/plugin.json"),
    "marketplace.json": Path(".claude-plugin/marketplace.json"),
    "codex plugin.json": Path(".codex-plugin/plugin.json"),
}


def version_of_record(root: Path) -> str:
    with (root / "pyproject.toml").open("rb") as fh:
        data = tomllib.load(fh)
    return data["project"]["version"]


def skill_versions(skills_dir: Path) -> dict[str, str | None]:
    """Map skill name -> declared metadata.version (None if missing/unreadable)."""
    versions: dict[str, str | None] = {}
    if not skills_dir.is_dir():
        return versions
    for child in sorted(skills_dir.iterdir()):
        skill_md = child / "SKILL.md"
        if not skill_md.is_file():
            continue
        try:
            data, _ = lint_skills.parse_frontmatter(skill_md.read_text(encoding="utf-8"))
        except lint_skills.FrontmatterError:
            versions[child.name] = None
            continue
        metadata = data.get("metadata")
        versions[child.name] = metadata.get("version") if isinstance(metadata, dict) else None
    return versions


def manifest_version_entries(label: str, path: Path) -> list[tuple[str, object]]:
    """Return ``(description, version)`` for each version field in a manifest."""
    data = json.loads(path.read_text(encoding="utf-8"))
    entries: list[tuple[str, object]] = []
    if isinstance(data, dict):
        if "version" in data:
            entries.append((label, data["version"]))
        for i, plugin in enumerate(data.get("plugins", []) or []):
            if isinstance(plugin, dict) and "version" in plugin:
                entries.append((f"{label} plugins[{i}]", plugin["version"]))
    return entries


def run_check(root: Path, *, require_manifests: bool = False) -> tuple[str, list[str], list[str]]:
    vor = version_of_record(root)
    errors: list[str] = []
    absent: list[str] = []

    for name, version in skill_versions(root / "skills").items():
        if version != vor:
            errors.append(
                f"skills/{name}/SKILL.md metadata.version={version!r} != {vor!r}"
            )

    init_path = root / PACKAGE_INIT
    if init_path.exists():
        match = re.search(r'^__version__ = "([^"]*)"', init_path.read_text(encoding="utf-8"), re.M)
        found = match.group(1) if match else None
        if found != vor:
            errors.append(f"{PACKAGE_INIT} __version__={found!r} != {vor!r}")

    for label, rel in MANIFESTS.items():
        path = root / rel
        if not path.exists():
            absent.append(label)
            if require_manifests:
                errors.append(f"required manifest absent: {label}")
            continue
        for desc, version in manifest_version_entries(label, path):
            if version != vor:
                errors.append(f"{desc} version={version!r} != {vor!r}")
    return vor, errors, absent


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check version agreement across the repo.")
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument(
        "--allow-absent-manifests",
        action="store_true",
        help="do not fail when a package manifest is missing",
    )
    args = parser.parse_args(argv)
    root = Path(args.root)

    vor, errors, absent = run_check(root, require_manifests=not args.allow_absent_manifests)
    print(f"version of record: {vor}")
    if absent:
        print("absent manifests: " + ", ".join(absent))
    for message in errors:
        print(message)
    if errors:
        print(f"version agreement: {len(errors)} mismatch(es)", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
