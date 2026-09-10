"""Content plan: select, order, and emphasize evidence within the template's page budget.

``plan`` reads the requirement map, the profile, and the template manifest, and produces a
ContentPlan: one unit per selected fact (carrying the `source_ids` it derives from and an
emphasis set by the chosen positioning), plus a cut list for anything the page budget or a
section's `max_items` cannot fit. Gap requirements contribute no evidence, so no gap is
ever cited as satisfied. Switching positioning re-emphasizes and reorders without changing
any fact.

Unit text follows two conventions the templates rely on: the contact unit is two lines
(the name, then the details line), and an experience unit separates the role from its
dates with a tab, followed, when the section sets ``role_summaries``, by the role's summary
on a second line. A résumé's experience section is reverse-chronological, each role
followed by its own achievements; positioning orders the achievements within a role and
every section outside the chronology. The contact unit and a role that still has
achievements in the plan are never cut for the page budget.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

from . import config as config_module
from . import schema
from .errors import CareerDocsError
from .providers import load_provider

_EMPHASIS_WEIGHT = {"high": 0, "medium": 1, "low": 2}
_DEFAULT_UNITS_PER_PAGE = 12
_MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


def is_visible(entity: dict) -> bool:
    return entity.get("visibility") != "private" and entity.get("verification") != "unverified"


def emphasis_for(entity: dict, positioning: str) -> str:
    tags = entity.get("positioning") or []
    if positioning in tags:
        return "high"
    if tags:  # tagged only for the other mode
        return "low"
    return "medium"


def display_date(value, *, default: str = "present") -> str:
    """``2021-06`` or ``2021-06-15`` → ``Jun 2021``; ``2021`` → ``2021``; empty → ``default``."""
    if not value:
        return default
    parts = str(value).split("-")
    year = parts[0]
    if len(parts) >= 2 and parts[1].isdigit() and 1 <= int(parts[1]) <= 12:
        return f"{_MONTHS[int(parts[1]) - 1]} {year}"
    return year


def display_link(url: str) -> str:
    """``https://www.linkedin.com/in/handle/`` → ``linkedin.com/in/handle``: the scheme,
    ``www.``, and a trailing slash dropped. The target keeps the full URL; render makes the
    display form clickable."""
    bare = re.sub(r"^https?://", "", url.strip())
    bare = re.sub(r"^www\.", "", bare)
    return bare.rstrip("/")


def _entity_text(entity: dict, section: dict | None = None) -> str:
    etype = entity["type"]
    if etype == "achievement":
        return entity.get("statement", "")
    if etype == "experience":
        role = ", ".join(p for p in (entity.get("title"), entity.get("organization")) if p)
        start = display_date(entity.get("start_date"), default="")
        span = f"{start} – {display_date(entity.get('end_date'))}" if start else display_date(entity.get("end_date"))
        text = f"{role}\t{span}"
        # A section that opts in (``role_summaries``) carries the role's summary as a second
        # line, so the descriptor sits under the role line rather than inside it.
        summary = (entity.get("summary") or "").strip()
        if section and section.get("role_summaries") and summary:
            text += "\n" + summary
        return text
    if etype == "skill":
        return entity.get("name", "")
    if etype == "education":
        return ", ".join(p for p in (entity.get("degree"), entity.get("institution")) if p)
    if etype == "project":
        return entity.get("name", "")
    if etype == "contact":
        details = [entity.get("location"), entity.get("phone"), entity.get("email")]
        details += [display_link(link["url"]) for link in entity.get("links") or [] if link.get("url")]
        line = " · ".join(p for p in details if p)
        name = entity.get("name", "")
        return f"{name}\n{line}" if line else name
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


def _home_role(entity: dict, by_id: dict, role_by_org: dict) -> str | None:
    """The experience an achievement belongs under: its parent experience, or, for a
    project achievement, the (most recent) experience at the project's organization."""
    parent = by_id.get(entity.get("parent_id") or "")
    if not parent:
        return None
    if parent["type"] == "experience":
        return parent["id"]
    if parent["type"] == "project":
        return role_by_org.get(parent.get("organization") or "")
    return None


def _role_by_org(units: list[dict], by_id: dict) -> dict:
    roles = [by_id[u["source_ids"][0]] for u in units if by_id.get(u["source_ids"][0], {}).get("type") == "experience"]
    roles.sort(key=lambda e: e.get("start_date") or "", reverse=True)
    mapping: dict = {}
    for role in roles:
        mapping.setdefault(role.get("organization") or "", role["id"])
    return mapping


def _chronological(units: list[dict], by_id: dict) -> list[dict]:
    """Reverse-chronological roles, each followed by its own achievements (in emphasis
    order); units with no role among those kept follow the last role."""
    def entity_of(unit):
        return by_id.get(unit["source_ids"][0], {})

    roles = [u for u in units if entity_of(u).get("type") == "experience"]
    if not roles:
        return units
    roles.sort(key=lambda u: entity_of(u).get("start_date") or "", reverse=True)
    role_by_org = _role_by_org(units, by_id)
    grouped = {u["source_ids"][0]: [u] for u in roles}
    rest: list[dict] = []
    for unit in units:
        entity = entity_of(unit)
        if entity.get("type") == "experience":
            continue
        home = _home_role(entity, by_id, role_by_org) if entity.get("type") == "achievement" else None
        (grouped[home] if home in grouped else rest).append(unit)
    return [u for role in roles for u in grouped[role["source_ids"][0]]] + rest


def generate_plan(mapping: list[dict], profile: dict, template: dict, positioning: str,
                  *, voice=None, brief=None, baseline: bool = False, page_budget: int | None = None) -> dict:
    by_id = {e["id"]: e for e in profile["entities"]}
    if baseline:
        # A baseline has no target role: every visible entity is eligible evidence.
        cited = {e["id"] for e in profile["entities"] if is_visible(e)}
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

    for section in template["sections"]:
        types = set(section["entity_types"])
        pool = [
            e for e in profile["entities"]
            if e["type"] in types and is_visible(e) and (e["id"] in cited or e["type"] == "contact")
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
            source_ids = [entity["id"]]
            if entity["type"] == "achievement" and entity.get("parent_id"):
                source_ids.append(entity["parent_id"])
            units.append({
                "unit_id": "",
                "section_id": section["id"],
                "kind": _kind_for(entity, section),
                "text": _entity_text(entity, section),
                "source_ids": source_ids,
                "emphasis": emphasis_for(entity, positioning),
            })
        for entity in dropped:
            cuts.append({"entity_id": entity["id"], "reason": f"exceeds {section['id']} budget of {max_items}"})

    page_budget = page_budget or template.get("page_budget", 2)
    per_page = template.get("units_per_page", _DEFAULT_UNITS_PER_PAGE)
    cap = page_budget * per_page

    def protected(unit: dict) -> bool:
        entity = by_id.get(unit["source_ids"][0], {})
        if entity.get("type") == "contact":
            return True
        if entity.get("type") != "experience":
            return False
        role_by_org = _role_by_org(units, by_id)
        return any(
            _home_role(by_id.get(u["source_ids"][0], {}), by_id, role_by_org) == entity["id"]
            for u in units if by_id.get(u["source_ids"][0], {}).get("type") == "achievement"
        )

    while len(units) > cap:
        candidates = [i for i in range(len(units)) if not protected(units[i])] or list(range(len(units)))
        idx = max(candidates, key=lambda i: (_EMPHASIS_WEIGHT[units[i]["emphasis"]], i))
        removed = units.pop(idx)
        cuts.append({"entity_id": removed["source_ids"][0], "reason": f"exceeds page budget of {page_budget}"})

    ordered: list[dict] = []
    for section in template["sections"]:
        section_units = [u for u in units if u["section_id"] == section["id"]]
        if not is_letter and {"experience", "achievement"} <= set(section["entity_types"]):
            section_units = _chronological(section_units, by_id)
        ordered.extend(section_units)
    for number, unit in enumerate(ordered, start=1):
        unit["unit_id"] = f"u{number}"

    return {
        "positioning": positioning,
        "kind": template.get("kind", "resume"),
        "template": {"name": template.get("name"), "version": template.get("version")},
        "voice": voice,
        "page_budget": page_budget,
        "units": ordered,
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
    parser.add_argument("--page-budget", type=int, metavar="PAGES",
                        help="pages for this plan (default: the brief's approach, then the template)")
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
    profile = load_provider(args.workspace, cfg).read()
    template = load_template(args.workspace, cfg, args.kind)

    if args.baseline:
        positioning = args.positioning or cfg["workflow"]["positioning_default"]
        plan = generate_plan([], profile, template, positioning,
                             voice={"path": cfg["voice"]["path"]}, baseline=True,
                             page_budget=args.page_budget)
        out_dir = Path(args.workspace) / cfg["outputs"]["baselines_dir"] / positioning
    else:
        slug = _resolve_slug(args, cfg)
        app_dir = Path(args.workspace) / cfg["outputs"]["applications_dir"] / slug
        mapping = json.loads((app_dir / "map.json").read_text(encoding="utf-8"))
        brief_path = app_dir / "brief.json"
        brief = json.loads(brief_path.read_text(encoding="utf-8")) if brief_path.is_file() else None
        # The agreed approach on the brief supplies the defaults; flags override it.
        approach = (brief or {}).get("approach") or {}
        positioning = args.positioning or approach.get("positioning") or cfg["workflow"]["positioning_default"]
        page_budget = args.page_budget or (approach.get("resume_pages") if args.kind == "resume" else None)
        plan = generate_plan(mapping, profile, template, positioning,
                             voice={"path": cfg["voice"]["path"]}, brief=brief, page_budget=page_budget)
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
