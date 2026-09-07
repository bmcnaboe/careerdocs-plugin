#!/usr/bin/env python3
"""agent-layer vendored check — verifies this repo against its .agent-layer.json.

Standalone by design: runs with python3 stdlib only and needs NO agent-layer
checkout, so CI and collaborators get the same enforcement as the layer owner.
(This file is itself synced from agent-layer; edit it there, not here.)

Checks:
  * every synced file exists and its sha256 matches the record
  * CLAUDE.md, when present, is a pure pointer (its only content is `@AGENTS.md`)
  * the `.agents` mirror symlink points at `.claude` (when the record asks for it)
  * layer-managed settings keys are present in .claude/settings.json

Exit 0 clean, 1 on any failure.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

RECORD_NAME = ".agent-layer.json"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def find_root(start: Path) -> Path | None:
    for candidate in [start, *start.parents]:
        if (candidate / RECORD_NAME).is_file():
            return candidate
    return None


def is_subset(expected, actual) -> bool:
    """True when `expected` is structurally contained in `actual`."""
    if isinstance(expected, dict):
        return isinstance(actual, dict) and all(
            key in actual and is_subset(value, actual[key]) for key, value in expected.items()
        )
    return expected == actual


def main(argv: list[str]) -> int:
    root = Path(argv[1]).resolve() if len(argv) > 1 else find_root(Path.cwd().resolve())
    if root is None or not (root / RECORD_NAME).is_file():
        print(f"agent-layer-check: no {RECORD_NAME} found", file=sys.stderr)
        return 1
    record = json.loads((root / RECORD_NAME).read_text())
    problems: list[str] = []

    for entry in record.get("files", []):
        if entry.get("mode") != "synced":
            continue
        target = root / entry["path"]
        if not target.is_file():
            problems.append(f"missing synced file: {entry['path']}")
        elif sha256_file(target) != entry["sha256"]:
            problems.append(
                f"drifted synced file: {entry['path']} (layer-owned; edit "
                f"agent-layer/{entry['source']} and run `layer sync-project`)"
            )

    claude_md = root / "CLAUDE.md"
    if claude_md.is_file():
        import re

        # HTML comments are allowed (self-documenting pointer); content is not.
        stripped = re.sub(r"<!--.*?-->", "", claude_md.read_text(), flags=re.DOTALL).strip()
        if stripped != "@AGENTS.md":
            problems.append(
                "CLAUDE.md must be a pure pointer — `@AGENTS.md` plus optional HTML "
                "comments (conventions live in AGENTS.md)"
            )

    if record.get("mirror"):
        mirror = root / ".agents"
        if not mirror.is_symlink():
            problems.append(".agents must be a symlink to .claude (run `layer sync-project`)")
        else:
            import os

            if os.readlink(mirror) not in (".claude", "./.claude"):
                problems.append(f".agents points to {os.readlink(mirror)!r}, want '.claude'")

    for ignore_path in record.get("format_ignore") or []:
        ignore_file = root / ignore_path
        text = ignore_file.read_text() if ignore_file.is_file() else ""
        if "# >>> agent-layer:synced-files >>>" not in text:
            problems.append(f"{ignore_path} is missing the agent-layer synced-files block "
                            "(run `layer sync-project`)")
        else:
            missing = [
                entry["path"] for entry in record.get("files", [])
                if entry.get("mode") == "synced" and entry["path"] not in text
            ]
            if missing:
                problems.append(f"{ignore_path} block is missing {len(missing)} synced path(s) "
                                "(run `layer sync-project`)")

    managed = record.get("settings_managed")
    if managed:
        settings_path = root / ".claude" / "settings.json"
        settings = json.loads(settings_path.read_text()) if settings_path.is_file() else {}
        if not is_subset(managed, settings):
            problems.append(".claude/settings.json is missing layer-managed keys (run `layer sync-project`)")

    for problem in problems:
        print(f"agent-layer-check: {problem}", file=sys.stderr)
    synced_count = sum(1 for entry in record.get("files", []) if entry.get("mode") == "synced")
    print(f"agent-layer-check: {synced_count} synced file(s), {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
