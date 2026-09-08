#!/usr/bin/env python3
"""Install the careerdocs-plugin skills for ChatGPT / Codex.

Standard library only. Each skill in ``manifest.json`` is linked (default) or copied into
``$HOME/.agents/skills/<name>`` — the location Codex discovers skills from. Use ``--copy``
for a standalone copy, ``--home`` to target a different home, ``--dry-run`` to preview, and
``--uninstall`` to remove them. The installer refuses to run when the manifest disagrees
with the ``skills/`` tree, and prints the manual ChatGPT upload steps after installing.

Usage:
    python3 packages/openai/install.py [--link | --copy] [--home DIR] [--dry-run]
    python3 packages/openai/install.py --uninstall [--home DIR] [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
MANIFEST_PATH = HERE / "manifest.json"


def load_manifest(path: Path = MANIFEST_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def discover_skills(root: Path) -> set[str]:
    skills_dir = root / "skills"
    if not skills_dir.is_dir():
        return set()
    return {c.name for c in skills_dir.iterdir() if (c / "SKILL.md").is_file()}


def verify(root: Path, manifest: dict) -> list[str]:
    listed = {s["name"] for s in manifest.get("skills", [])}
    present = discover_skills(root)
    errors: list[str] = []
    if listed != present:
        errors.append(f"manifest skills {sorted(listed)} disagree with skills/ {sorted(present)}")
    for skill in manifest.get("skills", []):
        if not (root / skill["path"]).is_dir():
            errors.append(f"manifest path {skill['path']!r} does not exist")
    return errors


def target_base(home: Path) -> Path:
    return home / ".agents" / "skills"


def _remove(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


def install(root: Path, manifest: dict, home: Path, *, mode: str = "link", dry_run: bool = False) -> list[str]:
    base = target_base(home)
    actions: list[str] = []
    for skill in manifest.get("skills", []):
        source = (root / skill["path"]).resolve()
        target = base / skill["name"]
        actions.append(f"{mode} {target} -> {source}")
        if dry_run:
            continue
        base.mkdir(parents=True, exist_ok=True)
        _remove(target)
        if mode == "link":
            target.symlink_to(source, target_is_directory=True)
        else:
            shutil.copytree(source, target)
    return actions


def uninstall(manifest: dict, home: Path, *, dry_run: bool = False) -> list[str]:
    base = target_base(home)
    actions: list[str] = []
    for skill in manifest.get("skills", []):
        target = base / skill["name"]
        if target.exists() or target.is_symlink():
            actions.append(f"remove {target}")
            if not dry_run:
                _remove(target)
    return actions


CHATGPT_STEPS = """\
ChatGPT upload (manual):
  1. In ChatGPT, open Settings → Skills (or the skill upload dialog).
  2. For each skill under skills/<name>/, upload its SKILL.md and referenced files.
  3. Keep the skill name identical to the directory name so invocations match Codex.
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Install careerdocs-plugin skills for ChatGPT/Codex.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--link", dest="mode", action="store_const", const="link", help="symlink (default)")
    mode.add_argument("--copy", dest="mode", action="store_const", const="copy", help="copy instead of symlink")
    parser.add_argument("--home", default=None, help="target home (default: $HOME)")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--uninstall", action="store_true")
    parser.set_defaults(mode="link")
    args = parser.parse_args(argv)

    manifest = load_manifest()
    errors = verify(REPO_ROOT, manifest)
    if errors:
        for message in errors:
            print(message, file=sys.stderr)
        return 2

    home = Path(args.home).expanduser() if args.home else Path.home()

    if args.uninstall:
        for action in uninstall(manifest, home, dry_run=args.dry_run):
            print(action)
        return 0

    for action in install(REPO_ROOT, manifest, home, mode=args.mode, dry_run=args.dry_run):
        print(action)
    if not args.dry_run:
        print()
        print(CHATGPT_STEPS)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
