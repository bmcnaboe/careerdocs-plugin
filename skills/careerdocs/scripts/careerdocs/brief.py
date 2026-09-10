"""Role brief: turn a job description into a structured skeleton the agent completes.

``brief <jd-file>`` extracts requirement skeletons (each with a stable id and a must/nice
kind), pulls keywords, and recommends a positioning mode, writing
``<applications_dir>/<slug>/brief.json``. The agent fills in the organization, role, and
any nuance; ``brief --validate <brief.json>`` checks the completed brief against the schema
and its invariants. ``brief --coverage <brief.json>`` reports which requirement keywords
appear literally in the visible profile and which do not — a prompt for judgement (a
synonym to reword, or a genuinely held skill to add through the update flow with the
applicant's yes), never an automatic addition. Deterministic and offline; a URL job
description is saved to a file first, then passed in.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from . import config as config_module
from . import ids, schema, util
from .errors import CareerDocsError
from .plan import is_visible

_STOPWORDS = {
    "the", "and", "for", "with", "you", "our", "your", "will", "are", "has", "have",
    "a", "an", "of", "to", "in", "on", "or", "as", "is", "be", "we", "at", "by",
    "that", "this", "from", "including", "such", "across", "into", "years", "year",
    "experience", "team", "teams", "work", "working", "must", "nice", "plus",
}
_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9+#.\-]*")

_MUST_MARKERS = ("(must)", "required", "must have", "must-have")
_NICE_MARKERS = ("(nice)", "preferred", "nice to have", "nice-to-have", "bonus", "a plus")

_EXECUTIVE_SIGNALS = ("lead", "leader", "leadership", "manage", "manager", "director",
                      "strategy", "strategic", "stakeholder", "roadmap", "organization",
                      "vision", "executive", "head")
_BUILDER_SIGNALS = ("hands-on", "build", "code", "coding", "implement", "engineer",
                    "engineering", "python", "go", "rust", "kubernetes", "systems",
                    "operate", "operating", "ship", "shipping", "production")


def _keywords(text: str, limit: int = 8) -> list[str]:
    seen: list[str] = []
    for token in _TOKEN_RE.findall(text):
        low = token.lower().strip(".-")
        if len(low) <= 2 or low in _STOPWORDS or low in seen:
            continue
        seen.append(low)
        if len(seen) >= limit:
            break
    return seen


def _kind(line: str) -> str:
    low = line.lower()
    if any(marker in low for marker in _NICE_MARKERS):
        return "nice"
    return "must"


def _strip_markers(line: str) -> str:
    text = re.sub(r"\((must|nice)\)", "", line, flags=re.IGNORECASE)
    return text.strip(" -*\t").strip()


def _requirement_lines(text: str) -> list[str]:
    lines = []
    in_requirements = False
    for raw in text.splitlines():
        stripped = raw.strip()
        if stripped.startswith("#"):
            in_requirements = "requirement" in stripped.lower()
            continue
        if stripped.startswith(("- ", "* ")):
            content = stripped[2:].strip()
            if in_requirements or any(m in content.lower() for m in _MUST_MARKERS + _NICE_MARKERS):
                lines.append(content)
    return lines


def recommend_positioning(text: str) -> str:
    low = text.lower()
    executive = sum(low.count(s) for s in _EXECUTIVE_SIGNALS)
    builder = sum(low.count(s) for s in _BUILDER_SIGNALS)
    return "executive" if executive > builder else "builder"


def generate_brief(jd_text: str, source: dict | None = None) -> dict:
    requirements = []
    for index, line in enumerate(_requirement_lines(jd_text), start=1):
        text = _strip_markers(line)
        requirements.append({
            "id": f"req-{index}",
            "text": text,
            "kind": _kind(line),
            "keywords": _keywords(text),
        })
    return {
        "organization": "",
        "role": "",
        "seniority": "",
        "location": "",
        "source": source,
        "requirements": requirements,
        "keywords": _keywords(jd_text, limit=16),
        "recommended_positioning": recommend_positioning(jd_text),
        "notes": "",
    }


_CONTENT_FIELDS = ("name", "title", "headline", "organization", "location", "statement", "summary",
                   "degree", "field_of_study", "role", "venue", "level")


def keyword_coverage(brief: dict, profile: dict) -> list[dict]:
    """Each requirement keyword, whether it appears literally (case-insensitive) in the
    visible profile's content fields, and the requirements that use it."""
    blob = " ".join(
        str(entity.get(field) or "")
        for entity in profile["entities"] if is_visible(entity)
        for field in _CONTENT_FIELDS
    ).lower()
    rows: dict[str, dict] = {}
    for requirement in brief["requirements"]:
        for keyword in requirement.get("keywords", []):
            row = rows.setdefault(keyword.lower(), {"keyword": keyword, "present": keyword.lower() in blob, "requirement_ids": []})
            row["requirement_ids"].append(requirement["id"])
    return list(rows.values())


def validate_brief(brief: dict) -> list[str]:
    errors = [f"schema: {e}" for e in schema.validate_against("role-brief", brief)]
    if errors:
        return errors
    seen: set[str] = set()
    for requirement in brief["requirements"]:
        if requirement["id"] in seen:
            errors.append(f"duplicate requirement id {requirement['id']!r}")
        seen.add(requirement["id"])
    return errors


# --- CLI ---


def register(subparsers, common: argparse.ArgumentParser) -> None:
    parser = subparsers.add_parser("brief", parents=[common], help="build or validate a role brief")
    parser.add_argument("input", help="job-description file, or a brief.json with --validate")
    parser.add_argument("--role-slug", help="application slug (default: derived from the path)")
    parser.add_argument("--validate", action="store_true", help="validate a completed brief")
    parser.add_argument("--coverage", action="store_true",
                        help="report which of a brief's requirement keywords the profile lacks")
    parser.set_defaults(func=cmd_brief)


def _slug_for(args, cfg: dict, input_path: Path) -> str:
    if args.role_slug:
        return args.role_slug
    applications = cfg["outputs"]["applications_dir"]
    for parent in input_path.resolve().parents:
        if parent.parent.name == applications:
            return parent.name
    return input_path.stem


def cmd_brief(args) -> int:
    cfg = config_module.resolve_config(args.workspace)
    input_path = Path(args.input)

    if args.validate:
        brief = json.loads(input_path.read_text(encoding="utf-8"))
        errors = validate_brief(brief)
        for message in errors:
            print(message)
        if errors:
            raise CareerDocsError("role brief is invalid", exit_code=1)
        print(json.dumps({"valid": True}) if args.json else "role brief is valid")
        return 0

    if args.coverage:
        from .providers import load_provider

        brief = json.loads(input_path.read_text(encoding="utf-8"))
        rows = keyword_coverage(brief, load_provider(args.workspace, cfg).read())
        missing = [row for row in rows if not row["present"]]
        if args.json:
            print(json.dumps({"keywords": rows, "missing": [row["keyword"] for row in missing]}))
        else:
            print(f"{len(rows) - len(missing)} of {len(rows)} requirement keyword(s) appear in the profile")
            for row in missing:
                print(f"missing: {row['keyword']} ({', '.join(row['requirement_ids'])})")
        return 0

    jd_text = input_path.read_text(encoding="utf-8")
    source = {
        "source_id": ids.new_source_id(),
        "kind": "note",
        "location": str(input_path),
        "sha256": hashlib.sha256(jd_text.encode("utf-8")).hexdigest(),
        "captured_at": util.now(),
    }
    brief = generate_brief(jd_text, source)

    slug = _slug_for(args, cfg, input_path)
    out_dir = Path(args.workspace) / cfg["outputs"]["applications_dir"] / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "brief.json"
    out_path.write_text(json.dumps(brief, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if args.json:
        print(json.dumps({"brief": str(out_path), "requirements": len(brief["requirements"]),
                          "recommended_positioning": brief["recommended_positioning"]}))
    else:
        print(f"wrote {out_path} — {len(brief['requirements'])} requirement skeleton(s)")
        print(f"recommended positioning: {brief['recommended_positioning']}")
    return 0
