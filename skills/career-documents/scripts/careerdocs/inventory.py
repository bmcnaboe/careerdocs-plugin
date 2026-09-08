"""Classify every file in a workspace directory ahead of a migration.

``inventory <dir>`` walks a directory and classifies each file as authoritative data,
source evidence, template/voice input, generated output, a historical record, a duplicate
(by sha256), temporary, or unrelated — and proposes a recoverable destination for each, so
nothing is discarded without somewhere to go. It writes ``inventory.json`` and
``inventory.md`` for review; the ``organize`` command consumes the JSON.

The classification is heuristic (name + location + content hash); a human reviews the
result before ``organize`` moves anything.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

CATEGORIES = (
    "authoritative_data", "source_evidence", "template_voice", "generated_output",
    "historical_record", "duplicate", "temporary", "unrelated",
)

DESTINATION = {
    "authoritative_data": "sources/",
    "source_evidence": "sources/",
    "template_voice": "templates/",
    "generated_output": "baselines/",
    "historical_record": "archive/",
    "duplicate": "archive/duplicates/",
    "temporary": "archive/temporary/",
    "unrelated": "archive/unrelated/",
}

_SKIP_DIRS = {".career-documents", ".git", ".obsidian"}
_CAREER_KEYWORDS = ("resume", "cv", "cover", "letter", "portfolio", "bio")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _career_keyword(name: str) -> bool:
    return any(keyword in name for keyword in _CAREER_KEYWORDS)


def _looks_career(name: str) -> bool:
    return _career_keyword(name) or name.endswith((".docx", ".pdf"))


def classify(rel: Path) -> tuple[str, str]:
    """Return ``(category, reason)`` for one relative path (duplicates handled later)."""
    parts = [p.lower() for p in rel.parts]
    directories = parts[:-1]
    name = rel.name.lower()

    if name == ".ds_store" or name.startswith("~$") or name.endswith((".tmp", ".swp")):
        return "temporary", "editor/OS temporary file"
    if name == "resume_source_of_truth.md":
        return "authoritative_data", "applicant statement source of truth"
    if "story-draft" in name or "plugin-story" in name or (name.endswith(".md") and "linear" in name):
        return "temporary", "temporary ticket/story draft"
    if "brand_guidelines" in name or "voice" in name or "style-guide" in name or "styleguide" in name:
        return "template_voice", "voice / brand guidance"
    if "archive" in directories:
        if _career_keyword(name):
            return "historical_record", "archived career document"
        return "unrelated", "non-career item under archive/"
    if {"output", "outputs", "generated", "baselines"} & set(directories):
        return "generated_output", "previously generated output"
    if "linkedin" in name or (name.endswith(".csv") and any(k in name for k in ("connections", "positions", "export"))):
        return "source_evidence", "network export"
    if _looks_career(name):
        return "source_evidence", "resume/cover-letter source document"
    return "unrelated", "unrecognized item"


def _iter_files(root: Path):
    for path in sorted(root.rglob("*")):
        if path.is_dir():
            continue
        if any(part in _SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        yield path


def _pick_primary(group: list[dict]) -> dict:
    def key(entry):
        low_priority = 1 if entry["category"] in ("generated_output", "temporary", "unrelated") else 0
        return (low_priority, entry["path"].count("/"), entry["path"])

    return sorted(group, key=key)[0]


def build_inventory(root: Path) -> list[dict]:
    entries: list[dict] = []
    by_sha: dict[str, list[dict]] = defaultdict(list)
    for path in _iter_files(root):
        rel = path.relative_to(root)
        category, reason = classify(rel)
        sha = _sha256(path)
        entry = {"path": str(rel), "sha256": sha, "category": category,
                 "destination": DESTINATION[category], "reason": reason}
        entries.append(entry)
        by_sha[sha].append(entry)

    for group in by_sha.values():
        if len(group) <= 1:
            continue
        primary = _pick_primary(group)
        for entry in group:
            if entry is primary:
                continue
            entry["category"] = "duplicate"
            entry["destination"] = DESTINATION["duplicate"]
            entry["reason"] = f"duplicate of {primary['path']} (identical sha256)"
            entry["duplicate_of"] = primary["path"]
    return entries


def counts(entries: list[dict]) -> dict[str, int]:
    result = {category: 0 for category in CATEGORIES}
    for entry in entries:
        result[entry["category"]] += 1
    return result


def render_markdown(root: Path, entries: list[dict]) -> str:
    lines = [f"# Workspace inventory: {root}", "", "## Counts", ""]
    for category, count in counts(entries).items():
        lines.append(f"- {category}: {count}")
    lines += ["", "## Files", "", "| Path | Category | Destination | Reason |",
              "| --- | --- | --- | --- |"]
    for entry in entries:
        lines.append(f"| {entry['path']} | {entry['category']} | {entry['destination']} | {entry['reason']} |")
    return "\n".join(lines) + "\n"


def write_inventory(root: Path, entries: list[dict], out_dir: Path) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "inventory.json"
    md_path = out_dir / "inventory.md"
    json_path.write_text(
        json.dumps({"root": str(root), "counts": counts(entries), "files": entries}, indent=2) + "\n",
        encoding="utf-8",
    )
    md_path.write_text(render_markdown(root, entries), encoding="utf-8")
    return json_path, md_path


# --- CLI ---


def register(subparsers, common: argparse.ArgumentParser) -> None:
    parser = subparsers.add_parser("inventory", parents=[common], help="classify a workspace directory")
    parser.add_argument("dir", help="directory to inventory")
    parser.add_argument("--out", help="output directory (default: <dir>/.career-documents)")
    parser.set_defaults(func=cmd_inventory)


def cmd_inventory(args) -> int:
    root = Path(args.dir)
    out_dir = Path(args.out) if args.out else root / ".career-documents"
    entries = build_inventory(root)
    json_path, md_path = write_inventory(root, entries, out_dir)
    summary = counts(entries)
    if args.json:
        print(json.dumps({"inventory": str(json_path), "counts": summary}))
    else:
        print(f"wrote {json_path} and {md_path}")
        for category, count in summary.items():
            if count:
                print(f"  {category}: {count}")
    return 0
