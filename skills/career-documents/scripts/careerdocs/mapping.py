"""Requirement-to-evidence map.

``map`` proposes, for each requirement in the brief, the profile entities whose keywords or
skill names overlap it, and a classification the agent then confirms: **direct** (a skill
or strong keyword match), **transferable** (partial overlap), or **gap** (no real support).
A gap carries no evidence — the flow must never claim it. Validation checks every
requirement appears exactly once, gaps are empty, and classifications are valid.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from . import config as config_module
from . import schema
from .errors import CareerDocsError
from .providers import load_provider

_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9+#.\-]*")
_TEXT_FIELDS = (
    "name", "title", "organization", "summary", "statement", "category",
    "degree", "field_of_study", "institution", "role", "headline",
)
_DIRECT_RATIO = 0.5
_TRANSFERABLE_RATIO = 0.34


def _tokens(text: str) -> set[str]:
    return {t.lower().strip(".-") for t in _TOKEN_RE.findall(text)}


def entity_tokens(entity: dict) -> set[str]:
    tokens: set[str] = set()
    for field in _TEXT_FIELDS:
        value = entity.get(field)
        if isinstance(value, str):
            tokens |= _tokens(value)
    for tag in entity.get("tags", []):
        tokens |= _tokens(tag)
    return tokens


def _skill_name_tokens(entity: dict) -> set[str]:
    if entity["type"] == "skill" and entity.get("name"):
        return _tokens(entity["name"])
    return set()


def _evidence_candidates(profile: dict) -> list[dict]:
    return [
        e for e in profile["entities"]
        if e.get("visibility") != "private" and e.get("verification") != "unverified"
    ]


def generate_map(brief: dict, profile: dict) -> list[dict]:
    candidates = _evidence_candidates(profile)
    mapping: list[dict] = []
    for requirement in brief["requirements"]:
        keywords = set(requirement.get("keywords", []))
        evidence: list[dict] = []
        matched: set[str] = set()
        skill_direct = False
        for entity in candidates:
            hits = keywords & entity_tokens(entity)
            skill_tokens = _skill_name_tokens(entity)
            if skill_tokens and skill_tokens <= keywords:
                skill_direct = True
                hits |= skill_tokens
            if hits:
                evidence.append({
                    "entity_id": entity["id"],
                    "why": f"matches {', '.join(sorted(hits))}",
                })
                matched |= hits
        ratio = len(matched) / max(1, len(keywords))
        if skill_direct or ratio >= _DIRECT_RATIO:
            classification = "direct"
        elif ratio >= _TRANSFERABLE_RATIO:
            classification = "transferable"
        else:
            classification = "gap"
            evidence = []
        mapping.append({
            "requirement_id": requirement["id"],
            "classification": classification,
            "evidence": evidence,
            "note": "",
        })
    return mapping


def validate_map(mapping: list[dict], brief: dict) -> list[str]:
    errors = [f"schema: {e}" for e in schema.validate_against("requirement-map", mapping)]
    if errors:
        return errors
    brief_ids = [r["id"] for r in brief["requirements"]]
    mapped_ids = [m["requirement_id"] for m in mapping]
    for rid in brief_ids:
        count = mapped_ids.count(rid)
        if count != 1:
            errors.append(f"requirement {rid} appears {count} time(s), expected exactly one")
    for rid in mapped_ids:
        if rid not in brief_ids:
            errors.append(f"map references unknown requirement {rid}")
    for entry in mapping:
        if entry["classification"] == "gap" and entry["evidence"]:
            errors.append(f"{entry['requirement_id']}: gap must have no evidence")
    return errors


# --- CLI ---


def register(subparsers, common: argparse.ArgumentParser) -> None:
    parser = subparsers.add_parser("map", parents=[common], help="map requirements to evidence")
    parser.add_argument("--role-slug", help="application slug (default: the only one present)")
    parser.add_argument("--validate", metavar="MAP_JSON", help="validate a completed map")
    parser.set_defaults(func=cmd_map)


def _resolve_slug(args, cfg: dict) -> str:
    applications = Path(args.workspace) / cfg["outputs"]["applications_dir"]
    if args.role_slug:
        return args.role_slug
    slugs = [d.name for d in applications.iterdir() if (d / "brief.json").is_file()] if applications.is_dir() else []
    if len(slugs) == 1:
        return slugs[0]
    raise CareerDocsError("specify --role-slug (found %d applications with a brief)" % len(slugs), code="USAGE")


def cmd_map(args) -> int:
    cfg = config_module.resolve_config(args.workspace)
    applications = Path(args.workspace) / cfg["outputs"]["applications_dir"]

    if args.validate:
        map_path = Path(args.validate)
        mapping = json.loads(map_path.read_text(encoding="utf-8"))
        brief = json.loads((map_path.parent / "brief.json").read_text(encoding="utf-8"))
        errors = validate_map(mapping, brief)
        for message in errors:
            print(message)
        if errors:
            raise CareerDocsError("requirement map is invalid", exit_code=1)
        print(json.dumps({"valid": True}) if args.json else "requirement map is valid")
        return 0

    slug = _resolve_slug(args, cfg)
    brief = json.loads((applications / slug / "brief.json").read_text(encoding="utf-8"))
    profile = load_provider(args.workspace, cfg).read()
    mapping = generate_map(brief, profile)
    out_path = applications / slug / "map.json"
    out_path.write_text(json.dumps(mapping, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    counts = {c: sum(1 for m in mapping if m["classification"] == c) for c in ("direct", "transferable", "gap")}
    if args.json:
        print(json.dumps({"map": str(out_path), "counts": counts}))
    else:
        print(f"wrote {out_path} — direct {counts['direct']}, transferable {counts['transferable']}, gap {counts['gap']}")
    return 0
