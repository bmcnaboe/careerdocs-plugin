"""Content plan: select, order, and emphasize evidence within the template's page budget.

``plan`` reads the requirement map, the profile, and the template manifest, and produces a
ContentPlan: one unit per selected fact (carrying the `source_ids` it derives from and an
emphasis set by the chosen positioning), plus a cut list for anything the page budget or a
section's `max_items` cannot fit. Gap requirements contribute no evidence, so no gap is
ever cited as satisfied. Switching positioning re-emphasizes and reorders without changing
any fact.

A role plan also carries the identity profile's path and the brief's ``alignment`` so the
drafting step has the applicant's own through-line at hand and the output record can name
them. The brief's agreed ``approach`` may name the ``sections`` this document uses;
the rest of the manifest's sections stay empty, so one manifest serves every role.

Unit text follows conventions the templates rely on. The contact unit is two lines (the
name, then the details line). A dated unit — a role, a degree, an award, a credential, a
publication, a patent, an affiliation — separates its heading from its dates with a tab,
and its heading separates the lead (the title or institution) from the rest with ``" — "``:
``Title — Organization, Location<tab>Jan 2020 – present``. An experience unit adds the
role's summary on a second line when the section sets ``role_summaries``. A section may
``join`` its units into one line (interests), ``group_by`` a field into labeled lines
(skills by category), or stand for the ``summary``: one drafted sentence unit citing the
lead evidence.

A résumé's experience section is reverse-chronological: each role, its own achievements,
then the projects at that role's organization as sub-heads, each followed by its
achievements; a section that lists projects without roles lists each project followed by
its achievements. Citing an achievement brings its role (and its project) into the
section, since a role line is structure rather than evidence. Positioning orders the achievements within a role and every section
outside the chronology. The contact unit, the summary, and a role or project that still
has achievements in the plan are never cut for the page budget.
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
_SUMMARY_LEADS = 3
DASH = " — "


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


def display_year(value) -> str:
    return str(value).split("-")[0] if value else ""


def display_link(url: str) -> str:
    """``https://www.linkedin.com/in/handle/`` → ``linkedin.com/in/handle``: the scheme,
    ``www.``, and a trailing slash dropped. The target keeps the full URL; render makes the
    display form clickable."""
    bare = re.sub(r"^https?://", "", url.strip())
    bare = re.sub(r"^www\.", "", bare)
    return bare.rstrip("/")


def experience_kind(entity: dict) -> str:
    """An experience's kind; one without a ``kind`` is employment."""
    return entity.get("kind") or "employment"


def _span(entity: dict, start_field: str = "start_date", end_field: str = "end_date") -> str:
    start = display_date(entity.get(start_field), default="")
    if start:
        return f"{start} – {display_date(entity.get(end_field))}"
    return display_date(entity.get(end_field), default="")


def _heading(lead: str, rest: str) -> str:
    return f"{lead}{DASH}{rest}" if lead and rest else (lead or rest)


def _dated(heading: str, dates: str) -> str:
    return f"{heading}\t{dates}" if dates else heading


def _entity_text(entity: dict, section: dict | None = None) -> str:
    etype = entity["type"]
    if etype == "achievement":
        return entity.get("statement", "")
    if etype == "experience":
        where = ", ".join(p for p in (entity.get("organization"), entity.get("location")) if p)
        text = _dated(_heading(entity.get("title", ""), where), _span(entity))
        # A section that opts in (``role_summaries``) carries the role's summary as a second
        # line, so the descriptor sits under the role line rather than inside it.
        summary = (entity.get("summary") or "").strip()
        if section and section.get("role_summaries") and summary:
            text += "\n" + summary
        return text
    if etype == "skill":
        return entity.get("name", "")
    if etype == "education":
        degree = ", ".join(p for p in (entity.get("degree"), entity.get("field_of_study")) if p)
        year = display_year(entity.get("end_date")) or (
            f"{display_year(entity.get('start_date'))} – present" if entity.get("start_date") else "")
        return _dated(_heading(entity.get("institution", ""), degree), year)
    if etype == "project":
        return _heading(entity.get("name", ""), (entity.get("summary") or "").strip())
    if etype == "credential":
        return _dated(_heading(entity.get("name", ""), entity.get("issuer", "")), display_year(entity.get("issued_date")))
    if etype == "patent":
        when = display_year(entity.get("grant_date")) or ("pending" if entity.get("status") == "pending" else "")
        return _dated(entity.get("title", ""), when)
    if etype == "publication":
        return _dated(_heading(entity.get("title", ""), entity.get("venue", "")), display_year(entity.get("date")))
    if etype == "award":
        return _dated(_heading(entity.get("title", ""), entity.get("issuer", "")), display_year(entity.get("date")))
    if etype == "interest":
        return entity.get("name", "")
    if etype == "affiliation":
        return _dated(_heading(entity.get("role", ""), entity.get("organization", "")), _span(entity))
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
    if entity["type"] == "achievement":
        return "bullet"
    if entity["type"] == "project" and "experience" in section.get("entity_types", []):
        return "subhead"  # a project folded under the role at its organization
    return "field"


def _is_contact_section(section: dict) -> bool:
    return section.get("placeholder") == "contact" or "contact" in section.get("entity_types", [])


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


def _norm(value) -> str:
    return " ".join(str(value).lower().split()) if value else ""


def _home(entity: dict, by_id: dict, placed: set[str], role_by_org: dict) -> str | None:
    """Where an achievement belongs among the placed units: its parent role, its parent
    project when that project is placed, else the (most recent) placed role at the
    project's organization."""
    parent = by_id.get(entity.get("parent_id") or "")
    if not parent:
        return None
    if parent["id"] in placed:
        return parent["id"]
    if parent["type"] == "project":
        return role_by_org.get(_norm(parent.get("organization")))
    return None


def _role_by_org(units: list[dict], by_id: dict) -> dict:
    roles = [by_id[u["source_ids"][0]] for u in units if by_id.get(u["source_ids"][0], {}).get("type") == "experience"]
    roles.sort(key=lambda e: e.get("start_date") or "", reverse=True)
    mapping: dict = {}
    for role in roles:
        mapping.setdefault(_norm(role.get("organization")), role["id"])
    return mapping


def _arrange(units: list[dict], by_id: dict) -> list[dict]:
    """Reverse-chronological roles, each followed by its own achievements (in emphasis
    order) and then the projects at its organization, each with its achievements; projects
    with no role among those kept follow, each with its achievements; anything left
    follows the last of them."""
    def entity_of(unit):
        return by_id.get(unit["source_ids"][0], {})

    roles = sorted((u for u in units if entity_of(u).get("type") == "experience"),
                   key=lambda u: entity_of(u).get("start_date") or "", reverse=True)
    projects = [u for u in units if entity_of(u).get("type") == "project"]
    if not roles and not projects:
        return units
    placed = {u["source_ids"][0] for u in roles + projects}
    role_by_org = _role_by_org(units, by_id)
    under: dict[str, list[dict]] = defaultdict(list)
    rest: list[dict] = []
    for unit in units:
        entity = entity_of(unit)
        if entity.get("type") in ("experience", "project"):
            continue
        home = _home(entity, by_id, placed, role_by_org) if entity.get("type") == "achievement" else None
        (under[home] if home in placed else rest).append(unit)

    project_units = {u["source_ids"][0]: u for u in projects}
    projects_by_role: dict[str, list[dict]] = defaultdict(list)
    orphan_projects: list[dict] = []
    for unit in sorted(projects, key=lambda u: entity_of(u).get("start_date") or "", reverse=True):
        role_id = role_by_org.get(_norm(entity_of(unit).get("organization"))) if roles else None
        (projects_by_role[role_id] if role_id else orphan_projects).append(unit)

    def with_projects(role_unit: dict) -> list[dict]:
        role_id = role_unit["source_ids"][0]
        block = [role_unit] + under[role_id]
        for project in projects_by_role[role_id]:
            block += [project] + under[project["source_ids"][0]]
        return block

    ordered = [u for role in roles for u in with_projects(role)]
    if not roles:  # a projects section keeps the emphasis order the pool arrived in
        orphan_projects = [project_units[u["source_ids"][0]] for u in projects]
    for project in orphan_projects:
        ordered += [project] + under[project["source_ids"][0]]
    return ordered + rest


def _with_parents(pool: list[dict], types: set, kinds: set, by_id: dict, claimed: set, positioning: str) -> list[dict]:
    """The pool of a section that groups achievements under roles or projects. A cited
    achievement brings its parent into the section — the role, or the project and the
    role at the project's organization — because a role line is structure, not evidence;
    a project with no role among the section's roles is left for a projects section, and
    an achievement whose parent belongs elsewhere (another kind of role, a claimed
    entity) goes with it. Parents that hold a kept achievement come first, then the
    achievements, then any cited parent without one, each group in emphasis order, so a
    ``max_items`` cap trims evidence before structure."""
    def fits(entity: dict) -> bool:
        return (entity["type"] in types and is_visible(entity) and entity["id"] not in claimed
                and (entity["type"] != "experience" or not kinds or experience_kind(entity) in kinds))

    roles_by_org: dict[str, list[dict]] = defaultdict(list)
    for entity in by_id.values():
        if entity["type"] == "experience" and fits(entity):
            roles_by_org[_norm(entity.get("organization"))].append(entity)

    def role_at(organization) -> dict | None:
        roles = sorted(roles_by_org.get(_norm(organization), []), key=lambda e: e.get("start_date") or "", reverse=True)
        return roles[0] if roles else None

    parents: dict[str, dict] = {}
    achievements: list[dict] = []
    for entity in pool:
        if entity["type"] != "achievement":
            continue
        parent = by_id.get(entity.get("parent_id") or "")
        if parent is None:
            continue
        if parent["type"] == "experience":
            if not fits(parent):
                continue
            parents[parent["id"]] = parent
        else:
            role = role_at(parent.get("organization"))
            if "project" in types and fits(parent) and (role is not None or "experience" not in types):
                parents[parent["id"]] = parent
                if role is not None:
                    parents[role["id"]] = role
            elif "project" not in types and role is not None:
                parents[role["id"]] = role
            else:
                continue
        achievements.append(entity)

    def by_emphasis(entities):
        return sorted(entities, key=lambda e: _EMPHASIS_WEIGHT[emphasis_for(e, positioning)])

    orgs = {_norm(e.get("organization")) for e in pool if e["type"] == "experience"} | {
        _norm(e.get("organization")) for e in parents.values() if e["type"] == "experience"}
    others = [e for e in pool if e["type"] in ("experience", "project") and e["id"] not in parents
              and (e["type"] != "project" or "experience" not in types or _norm(e.get("organization")) in orgs)]
    return by_emphasis(parents.values()) + by_emphasis(achievements) + by_emphasis(others)


def _unit(entity: dict, section: dict, positioning: str) -> dict:
    source_ids = [entity["id"]]
    if entity["type"] == "achievement" and entity.get("parent_id"):
        source_ids.append(entity["parent_id"])
    return {
        "unit_id": "",
        "section_id": section["id"],
        "kind": _kind_for(entity, section),
        "text": _entity_text(entity, section),
        "source_ids": source_ids,
        "emphasis": emphasis_for(entity, positioning),
    }


def _merge_units(units: list[dict], text: str, kind: str) -> dict:
    return {
        "unit_id": "",
        "section_id": units[0]["section_id"],
        "kind": kind,
        "text": text,
        "source_ids": [sid for unit in units for sid in unit["source_ids"]],
        "emphasis": min((u["emphasis"] for u in units), key=_EMPHASIS_WEIGHT.get),
    }


def _joined(units: list[dict], section: dict) -> list[dict]:
    """``join``: one line holding every unit's text, citing every unit's sources."""
    if not units:
        return []
    return [_merge_units(units, section["join"].join(u["text"] for u in units), section.get("kind") or "field")]


def _grouped(units: list[dict], entities: dict, section: dict) -> list[dict]:
    """``group_by``: one ``Label<tab>a, b, c`` line per distinct value of the field, in the
    order the values first appear; units without the field share an unlabeled line."""
    field = section["group_by"]
    groups: dict[str, list[dict]] = {}
    for unit in units:
        groups.setdefault(entities[unit["source_ids"][0]].get(field) or "", []).append(unit)
    merged = []
    for label, members in groups.items():
        names = ", ".join(u["text"] for u in members)
        merged.append(_merge_units(members, f"{label}\t{names}" if label else names, section.get("kind") or "labeled"))
    return merged


def _summary_unit(section: dict, entities: list[dict], cited: set[str], positioning: str,
                  brief: dict | None) -> dict | None:
    """The one drafted unit of a ``summary`` section: its text starts as the contact's
    headline (else the most recent cited role) and its sources are the lead evidence — the
    approach's ``lead_evidence`` when the brief names it, else the strongest cited
    entities of the section's types — so the drafting step can write the summary those
    entities support."""
    contact = next((e for e in entities if e["type"] == "contact" and is_visible(e)), None)
    if contact is None:
        return None
    by_id = {e["id"]: e for e in entities}
    leads = [i for i in ((brief or {}).get("approach") or {}).get("lead_evidence", [])
             if i in by_id and i in cited and is_visible(by_id[i])]
    if not leads:
        types = set(section.get("entity_types") or ["experience", "achievement", "skill", "project"])
        pool = [e for e in entities if e["type"] in types and e["id"] in cited and is_visible(e)]
        pool.sort(key=lambda e: (_EMPHASIS_WEIGHT[emphasis_for(e, positioning)], -(len(e.get("start_date") or ""))))
        leads = [e["id"] for e in pool[:_SUMMARY_LEADS]]
    roles = sorted((e for e in entities if e["type"] == "experience" and e["id"] in cited and is_visible(e)),
                   key=lambda e: e.get("start_date") or "", reverse=True)
    text = contact.get("headline") or (f"{roles[0].get('title', '')}, {roles[0].get('organization', '')}" if roles else "")
    return {
        "unit_id": "",
        "section_id": section["id"],
        "kind": section.get("kind") or "sentence",
        "text": text,
        "source_ids": [contact["id"]] + [i for i in leads if i != contact["id"]],
        "emphasis": "high",
    }


def generate_plan(mapping: list[dict], profile: dict, template: dict, positioning: str,
                  *, voice=None, identity=None, alignment=None, brief=None, baseline: bool = False,
                  page_budget: int | None = None, sections=None) -> dict:
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
    wanted = set(sections) if sections else None
    units: list[dict] = []
    cuts: list[dict] = []
    claimed: set[str] = set()

    for section in template["sections"]:
        if wanted is not None and section["id"] not in wanted and not _is_contact_section(section):
            continue
        if section.get("placeholder") == "summary":
            summary = _summary_unit(section, profile["entities"], cited, positioning, brief)
            if summary:
                units.append(summary)
            continue
        types = set(section["entity_types"])
        kinds = set(section.get("experience_kinds") or [])
        pool = [
            e for e in profile["entities"]
            if e["type"] in types and is_visible(e) and (e["id"] in cited or e["type"] == "contact")
            and e["id"] not in claimed
            and (e["type"] != "experience" or not kinds or experience_kind(e) in kinds)
        ]
        if is_letter:
            # A cover letter leads with the highest-value evidence, then emphasis.
            pool.sort(key=lambda e: (-values.get(e["id"], 0), _EMPHASIS_WEIGHT[emphasis_for(e, positioning)]))
        else:
            pool.sort(key=lambda e: _EMPHASIS_WEIGHT[emphasis_for(e, positioning)])
        if not is_letter and "achievement" in types and types & {"experience", "project"}:
            pool = _with_parents(pool, types, kinds, by_id, claimed, positioning)
        max_items = section.get("max_items")
        kept = pool[:max_items] if max_items is not None else pool
        dropped = pool[max_items:] if max_items is not None else []

        section_units = [_unit(entity, section, positioning) for entity in kept]
        claimed.update(entity["id"] for entity in kept)
        if section.get("join"):
            section_units = _joined(section_units, section)
        elif section.get("group_by"):
            section_units = _grouped(section_units, by_id, section)
        units += section_units
        for entity in dropped:
            cuts.append({"entity_id": entity["id"], "reason": f"exceeds {section['id']} budget of {max_items}"})

    page_budget = page_budget or template.get("page_budget", 2)
    per_page = template.get("units_per_page", _DEFAULT_UNITS_PER_PAGE)
    cap = page_budget * per_page

    def protected(unit: dict) -> bool:
        entity = by_id.get(unit["source_ids"][0], {})
        if entity.get("type") == "contact":
            return True
        if entity.get("type") not in ("experience", "project"):
            return False
        placed = {u["source_ids"][0] for u in units if by_id.get(u["source_ids"][0], {}).get("type") in ("experience", "project")}
        role_by_org = _role_by_org(units, by_id)
        return any(
            _home(by_id.get(u["source_ids"][0], {}), by_id, placed, role_by_org) == entity["id"]
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
        types = set(section.get("entity_types", []))
        if not is_letter and "achievement" in types and types & {"experience", "project"}:
            section_units = _arrange(section_units, by_id)
        ordered.extend(section_units)
    for number, unit in enumerate(ordered, start=1):
        unit["unit_id"] = f"u{number}"

    return {
        "positioning": positioning,
        "kind": template.get("kind", "resume"),
        "template": {"name": template.get("name"), "version": template.get("version")},
        "voice": voice,
        "identity": identity,
        "alignment": alignment,
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
                        help="pages for this plan (default: the brief's approach, then the configured default)")
    parser.add_argument("--sections", metavar="IDS",
                        help="comma-separated manifest section ids this document uses (default: the brief's approach, then every section)")
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


def _section_ids(value: str | None) -> list[str] | None:
    if not value:
        return None
    return [part.strip() for part in value.split(",") if part.strip()]


def cmd_plan(args) -> int:
    cfg = config_module.resolve_config(args.workspace)
    profile = load_provider(args.workspace, cfg).read()
    template = load_template(args.workspace, cfg, args.kind)

    voice = {"path": cfg["voice"]["path"]}
    identity = {"path": cfg["identity"]["path"]}
    if args.baseline:
        positioning = args.positioning or cfg["workflow"]["positioning_default"]
        page_budget = args.page_budget or (cfg["workflow"]["page_budget"]["resume"] if args.kind == "resume" else None)
        plan = generate_plan([], profile, template, positioning,
                             voice=voice, identity=identity, baseline=True,
                             page_budget=page_budget, sections=_section_ids(args.sections))
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
        page_budget = args.page_budget or (
            approach.get("resume_pages") or cfg["workflow"]["page_budget"]["resume"]
            if args.kind == "resume" else None
        )
        sections = _section_ids(args.sections) or (approach.get("sections") if args.kind == "resume" else None)
        plan = generate_plan(mapping, profile, template, positioning,
                             voice=voice, identity=identity, alignment=(brief or {}).get("alignment"),
                             brief=brief, page_budget=page_budget, sections=sections)
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
