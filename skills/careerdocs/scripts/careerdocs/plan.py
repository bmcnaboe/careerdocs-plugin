"""Content plan: select, order, and emphasize evidence within the template's page budget.

``plan`` reads the requirement map, the profile, and the template manifest, and produces a
ContentPlan: one unit per selected fact (carrying the `source_ids` it derives from and an
emphasis set by the chosen positioning), plus a cut list for anything the page budget or a
section's `max_items` cannot fit. Gap requirements contribute no evidence, so no gap is
ever cited as satisfied. Switching positioning re-emphasizes and reorders without changing
any fact.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from . import config as config_module
from . import schema
from .errors import CareerDocsError
from .providers import load_provider

_EMPHASIS_WEIGHT = {"high": 0, "medium": 1, "low": 2}
_DEFAULT_UNITS_PER_PAGE = 12


def _visible(entity: dict) -> bool:
    return entity.get("visibility") != "private" and entity.get("verification") != "unverified"


def emphasis_for(entity: dict, positioning: str) -> str:
    tags = entity.get("positioning") or []
    if positioning in tags:
        return "high"
    if tags:  # tagged only for the other mode
        return "low"
    return "medium"


def _entity_text(entity: dict) -> str:
    etype = entity["type"]
    if etype == "achievement":
        return entity.get("statement", "")
    if etype == "experience":
        span = f"{entity.get('start_date', '')}–{entity.get('end_date') or 'present'}"
        return f"{entity.get('title', '')}, {entity.get('organization', '')} ({span})".strip()
    if etype == "skill":
        return entity.get("name", "")
    if etype == "education":
        return ", ".join(p for p in (entity.get("degree"), entity.get("institution")) if p)
    if etype == "project":
        return entity.get("name", "")
    if etype == "contact":
        return " · ".join(
            p for p in (entity.get("name"), entity.get("email"), entity.get("phone"), entity.get("location")) if p
        )
    return entity.get("name") or entity.get("title") or ""


def _kind_for(entity: dict, section: dict) -> str:
    if section.get("kind"):
        return section["kind"]
    return "bullet" if entity["type"] == "achievement" else "field"


def value_scores(mapping: list[dict], brief: dict | None) -> dict[str, int]:
    """Score each cited entity by requirement value (must>nice, direct>transferable)."""
    kind_by_req = {r["id"]: r.get("kind", "must") for r in brief["requirements"]} if brief else {}
    scores: dict[str, int] = defaultdict(int)
    for entry in mapping:
        if entry["classification"] == "gap":
            continue
        base = 2 if entry["classification"] == "direct" else 1
        weight = 2 if kind_by_req.get(entry["requirement_id"], "must") == "must" else 1
        for ev in entry["evidence"]:
            scores[ev["entity_id"]] = max(scores[ev["entity_id"]], base * weight)
    return scores


def generate_plan(mapping: list[dict], profile: dict, template: dict, positioning: str,
                  *, voice=None, brief=None, baseline: bool = False) -> dict:
    if baseline:
        # A baseline has no target role: every visible entity is eligible evidence.
        cited = {e["id"] for e in profile["entities"] if _visible(e)}
    else:
        cited = {
            ev["entity_id"]
            for entry in mapping
            if entry["classification"] != "gap"
            for ev in entry["evidence"]
        }
    is_letter = template.get("kind") == "cover_letter"
    values = value_scores(mapping, brief) if is_letter else {}
    units: list[dict] = []
    cuts: list[dict] = []
    unit_no = 0

    for section in template["sections"]:
        types = set(section["entity_types"])
        pool = [
            e for e in profile["entities"]
            if e["type"] in types and _visible(e) and (e["id"] in cited or e["type"] == "contact")
        ]
        if is_letter:
            # A cover letter leads with the highest-value evidence, then emphasis.
            pool.sort(key=lambda e: (-values.get(e["id"], 0), _EMPHASIS_WEIGHT[emphasis_for(e, positioning)]))
        else:
            pool.sort(key=lambda e: _EMPHASIS_WEIGHT[emphasis_for(e, positioning)])
        max_items = section.get("max_items")
        kept = pool[:max_items] if max_items is not None else pool
        dropped = pool[max_items:] if max_items is not None else []

        for entity in kept:
            unit_no += 1
            source_ids = [entity["id"]]
            if entity["type"] == "achievement" and entity.get("parent_id"):
                source_ids.append(entity["parent_id"])
            units.append({
                "unit_id": f"u{unit_no}",
                "section_id": section["id"],
                "kind": _kind_for(entity, section),
                "text": _entity_text(entity),
                "source_ids": source_ids,
                "emphasis": emphasis_for(entity, positioning),
            })
        for entity in dropped:
            cuts.append({"entity_id": entity["id"], "reason": f"exceeds {section['id']} budget of {max_items}"})

    page_budget = template.get("page_budget", 2)
    per_page = template.get("units_per_page", _DEFAULT_UNITS_PER_PAGE)
    cap = page_budget * per_page
    while len(units) > cap:
        idx = max(range(len(units)), key=lambda i: (_EMPHASIS_WEIGHT[units[i]["emphasis"]], i))
        removed = units.pop(idx)
        cuts.append({"entity_id": removed["source_ids"][0], "reason": f"exceeds page budget of {page_budget}"})

    return {
        "positioning": positioning,
        "kind": template.get("kind", "resume"),
        "template": {"name": template.get("name"), "version": template.get("version")},
        "voice": voice,
        "page_budget": page_budget,
        "units": units,
        "cuts": cuts,
    }


def validate_plan(plan: dict, template: dict | None = None) -> list[str]:
    errors = [f"schema: {e}" for e in schema.validate_against("content-plan", plan)]
    if errors:
        return errors
    allowlist = set(template.get("allowlist", [])) if template else set()
    for unit in plan["units"]:
        if not unit["source_ids"] and unit["section_id"] not in allowlist:
            errors.append(f"unit {unit['unit_id']} has no source_ids and its section is not allowlisted")
    return errors


# --- CLI ---


def register(subparsers, common: argparse.ArgumentParser) -> None:
    parser = subparsers.add_parser("plan", parents=[common], help="build the content plan")
    parser.add_argument("--positioning", choices=["executive", "builder"])
    parser.add_argument("--kind", choices=["resume", "cover_letter"], default="resume")
    parser.add_argument("--role-slug")
    parser.add_argument("--baseline", action="store_true", help="role-less baseline from all visible evidence")
    parser.set_defaults(func=cmd_plan)


def load_template(workspace, cfg: dict, kind: str) -> dict:
    templates = cfg["templates"]
    sub = templates["resume"] if kind == "resume" else templates["cover_letter"]
    path = Path(workspace) / templates["dir"] / sub / "template.json"
    if not path.is_file():
        raise CareerDocsError(f"template manifest not found at {path}", code="USAGE")
    template = json.loads(path.read_text(encoding="utf-8"))
    template.setdefault("kind", kind)
    return template


def _resolve_slug(args, cfg: dict) -> str:
    applications = Path(args.workspace) / cfg["outputs"]["applications_dir"]
    if args.role_slug:
        return args.role_slug
    slugs = [d.name for d in applications.iterdir() if (d / "map.json").is_file()] if applications.is_dir() else []
    if len(slugs) == 1:
        return slugs[0]
    raise CareerDocsError("specify --role-slug", code="USAGE")


def cmd_plan(args) -> int:
    cfg = config_module.resolve_config(args.workspace)
    positioning = args.positioning or cfg["workflow"]["positioning_default"]
    profile = load_provider(args.workspace, cfg).read()
    template = load_template(args.workspace, cfg, args.kind)

    if args.baseline:
        plan = generate_plan([], profile, template, positioning,
                             voice={"path": cfg["voice"]["path"]}, baseline=True)
        out_dir = Path(args.workspace) / cfg["outputs"]["baselines_dir"] / positioning
    else:
        slug = _resolve_slug(args, cfg)
        app_dir = Path(args.workspace) / cfg["outputs"]["applications_dir"] / slug
        mapping = json.loads((app_dir / "map.json").read_text(encoding="utf-8"))
        brief_path = app_dir / "brief.json"
        brief = json.loads(brief_path.read_text(encoding="utf-8")) if brief_path.is_file() else None
        plan = generate_plan(mapping, profile, template, positioning,
                             voice={"path": cfg["voice"]["path"]}, brief=brief)
        out_dir = app_dir

    errors = validate_plan(plan, template)
    if errors:
        for message in errors:
            print(message)
        raise CareerDocsError("content plan is invalid", exit_code=1)

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "plan.json"
    out_path.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if args.json:
        print(json.dumps({"plan": str(out_path), "units": len(plan["units"]), "cuts": len(plan["cuts"]), "positioning": positioning}))
    else:
        print(f"wrote {out_path} — {len(plan['units'])} unit(s), {len(plan['cuts'])} cut(s), positioning {positioning}")
    return 0
