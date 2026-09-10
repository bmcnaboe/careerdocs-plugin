"""Render a content plan into the DOCX template, and record what was produced.

``render`` fills the template (docxtpl) from the content plan, writing a timestamped file
under the application's ``outputs/`` (never overwriting), and writes an output-record
skeleton beside it with the union of the plan's source ids and every check marked pending.
``--pdf`` converts via LibreOffice (`soffice`) when it is on PATH, and records the
conversion as skipped with a reason when it is not.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from . import __version__
from . import config as config_module
from . import plan as plan_module
from . import schema, util
from .errors import CareerDocsError
from .providers import load_provider

_PDF_CHECKS = ("pagination", "layout")
_ALL_CHECKS = ("factual", "links_dates", "extraction", "pagination", "layout")


def stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _unit_context(unit: dict) -> dict:
    # A tab splits a unit into a head and a tail (an experience unit's role and dates), so a
    # template can style the two halves — a bold role, a right-aligned date — separately.
    head, _, tail = unit["text"].partition("\t")
    return {"text": unit["text"], "kind": unit["kind"], "head": head, "tail": tail}


def build_context(plan: dict, template: dict) -> dict:
    by_section: dict[str, list] = defaultdict(list)
    for unit in plan["units"]:
        by_section[unit["section_id"]].append(unit)

    contact_text = ""
    sections = []
    for section in template["sections"]:
        units = by_section.get(section["id"], [])
        if section.get("placeholder") == "contact" or "contact" in section.get("entity_types", []):
            contact_text = units[0]["text"] if units else ""
            continue
        sections.append({
            "id": section["id"],
            "title": section.get("title", ""),
            "units": [_unit_context(u) for u in units],
        })
    # The contact unit is two lines: the name, then the details line.
    contact_name, _, contact_details = contact_text.partition("\n")
    return {
        "contact": contact_text,
        "contact_name": contact_name,
        "contact_details": contact_details,
        "positioning": plan["positioning"],
        "sections": sections,
    }


def render_document(plan: dict, template: dict, template_docx: Path, out_path: Path) -> None:
    from docxtpl import DocxTemplate

    doc = DocxTemplate(str(template_docx))
    doc.render(build_context(plan, template))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(out_path))


def convert_to_pdf(docx_path: Path) -> Path | None:
    if shutil.which("soffice") is None:
        return None
    subprocess.run(
        ["soffice", "--headless", "--convert-to", "pdf", "--outdir", str(docx_path.parent), str(docx_path)],
        check=True, capture_output=True, text=True,
    )
    pdf_path = docx_path.with_suffix(".pdf")
    return pdf_path if pdf_path.exists() else None


def build_record(plan: dict, *, document: Path, kind: str, positioning: str,
                 plan_path: Path | None, brief_path: Path | None, map_path: Path | None,
                 pdf_path: Path | None, pdf_available: bool) -> dict:
    source_ids = sorted({sid for unit in plan["units"] for sid in unit["source_ids"]})
    checks = {name: {"status": "pending", "details": ""} for name in _ALL_CHECKS}
    if not pdf_available:
        for name in _PDF_CHECKS:
            checks[name] = {"status": "skipped", "details": "no PDF (soffice not available)"}
    record = {
        "document": str(document),
        "kind": kind,
        "generated_at": util.now(),
        "plugin_version": __version__,
        "schema_version": schema.profile_schema_version(),
        "role_brief": str(brief_path) if brief_path else None,
        "map": str(map_path) if map_path else None,
        "content_plan": str(plan_path) if plan_path else None,
        "template": plan["template"],
        "voice": plan.get("voice"),
        "positioning": positioning,
        "source_ids": source_ids,
        "checks": checks,
        "stale": False,
        "stale_reason": None,
    }
    if pdf_path:
        record["pdf"] = str(pdf_path)
    return record


def _unique_path(directory: Path, base: str, suffix: str) -> Path:
    candidate = directory / f"{base}{suffix}"
    counter = 2
    while candidate.exists():
        candidate = directory / f"{base}-{counter}{suffix}"
        counter += 1
    return candidate


# --- CLI ---


def register(subparsers, common: argparse.ArgumentParser) -> None:
    parser = subparsers.add_parser("render", parents=[common], help="render a content plan into the template")
    parser.add_argument("--kind", choices=["resume", "cover_letter"], default="resume")
    parser.add_argument("--role-slug")
    parser.add_argument("--positioning", choices=["executive", "builder"], help="baseline positioning")
    parser.add_argument("--baseline", action="store_true", help="render a role-less baseline")
    parser.add_argument("--pdf", action="store_true", help="also produce a PDF (needs soffice)")
    parser.set_defaults(func=cmd_render)


def cmd_render(args) -> int:
    cfg = config_module.resolve_config(args.workspace)
    if args.baseline:
        positioning = args.positioning or cfg["workflow"]["positioning_default"]
        app_dir = Path(args.workspace) / cfg["outputs"]["baselines_dir"] / positioning
        brief_path = map_path = None
    else:
        slug = plan_module._resolve_slug(args, cfg)
        app_dir = Path(args.workspace) / cfg["outputs"]["applications_dir"] / slug
        brief_path = app_dir / "brief.json"
        map_path = app_dir / "map.json"

    plan_path = app_dir / "plan.json"
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    template = plan_module.load_template(args.workspace, cfg, args.kind)
    templates = cfg["templates"]
    sub = templates["resume"] if args.kind == "resume" else templates["cover_letter"]
    template_docx = Path(args.workspace) / templates["dir"] / sub / "template.docx"
    if not template_docx.is_file():
        raise CareerDocsError(f"template not found at {template_docx}", code="USAGE")

    # Baselines land directly under baselines/<positioning>/; role outputs under outputs/.
    out_dir = app_dir if args.baseline else app_dir / "outputs"
    out_docx = _unique_path(out_dir, f"{args.kind}-{stamp()}", ".docx")
    render_document(plan, template, template_docx, out_docx)

    pdf_path = None
    pdf_available = shutil.which("soffice") is not None
    if args.pdf:
        pdf_path = convert_to_pdf(out_docx)
        pdf_available = pdf_path is not None

    record = build_record(
        plan, document=out_docx, kind=args.kind, positioning=plan["positioning"],
        plan_path=plan_path,
        brief_path=brief_path if (brief_path and brief_path.is_file()) else None,
        map_path=map_path if (map_path and map_path.is_file()) else None,
        pdf_path=pdf_path, pdf_available=pdf_available,
    )
    invalid = schema.validate_against("output-record", record)
    if invalid:
        raise CareerDocsError("output record is invalid: " + "; ".join(invalid))
    record_path = out_docx.with_suffix(".record.json")
    record_path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if args.json:
        print(json.dumps({"document": str(out_docx), "pdf": str(pdf_path) if pdf_path else None, "record": str(record_path)}))
    else:
        print(f"rendered {out_docx}")
        if args.pdf:
            print(f"pdf: {pdf_path}" if pdf_path else "pdf: skipped (soffice not available)")
    return 0
