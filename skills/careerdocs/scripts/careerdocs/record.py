"""Run the five checks and record the verdict.

``check <document>`` extracts the document text, runs the factual, links/dates,
extraction, pagination, and layout checks (the last three need a PDF; skipped with a
reason when there is none), updates the output record, and exits 1 if any check failed.
A cover letter's factual check also fails when it reproduces a bullet of the résumé
rendered beside it. The layout check renders one PNG per page under
``.careerdocs/layout/<application>/`` in the workspace, out of the application folder.
A document is only "done" when its record shows every check passed or skipped.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import config as config_module
from . import plan as plan_module
from . import schema
from .checks import extraction, factual, layout, links_dates
from .errors import CareerDocsError
from .providers import load_provider

CHECK_NAMES = ("factual", "links_dates", "extraction", "pagination", "layout")


def _docx_text(path: Path) -> str:
    from docx import Document

    return "\n".join(p.text for p in Document(str(path)).paragraphs)


def document_text(document: Path) -> str:
    if document.suffix.lower() == ".pdf":
        return extraction.extract_text(document)
    return _docx_text(document)


def run_checks(text: str, pdf_path: Path | None, plan: dict, profile: dict, template: dict,
               *, layout_dir: Path | None = None, layout_name: str = "layout", template_lines=(),
               resume_bullets=()) -> dict:
    """``resume_bullets`` are the bullets of the résumé a cover letter accompanies; one
    reproduced verbatim fails the factual check."""
    allowlist = template.get("allowlist", []) if template else []
    results = {
        "factual": factual.check(text, plan, profile, allowlist=allowlist, template_lines=template_lines),
        "links_dates": links_dates.check(text),
    }
    if resume_bullets:
        verbatim = factual.verbatim_bullet_check(text, resume_bullets)
        if verbatim["status"] == "fail":
            details = verbatim["details"]
            if results["factual"]["status"] == "fail":
                details = results["factual"]["details"] + "; " + details
            results["factual"] = {"status": "fail", "details": details}
    if pdf_path is not None:
        results["extraction"] = extraction.check(pdf_path)
        results["pagination"] = pagination_check(pdf_path, plan)
        results["layout"] = layout.check(pdf_path, out_dir=layout_dir, name=layout_name,
                                         single_lines=contact_lines(plan))
    else:
        for name in ("extraction", "pagination", "layout"):
            results[name] = {"status": "skipped", "details": "no PDF (soffice not available)"}
    return results


def contact_lines(plan: dict) -> list[str]:
    """The contact unit's details line: the template sets it as one line, so it must fit."""
    for unit in plan["units"]:
        if unit["section_id"] == "header":
            return [line for line in unit["text"].splitlines()[1:] if line.strip()]
    return []


def pagination_check(pdf_path: Path, plan: dict) -> dict:
    from .checks import pagination

    return pagination.check(pdf_path, plan.get("page_budget", 2), exact=plan.get("kind") == "resume")


def validate_record(record: dict) -> list[str]:
    return schema.validate_against("output-record", record)


def apply_results(record: dict, results: dict) -> dict:
    record["checks"] = {name: results[name] for name in CHECK_NAMES}
    return record


def overall_exit_code(results: dict) -> int:
    return 1 if any(r["status"] == "fail" for r in results.values()) else 0


# --- CLI ---


def register(subparsers, common: argparse.ArgumentParser) -> None:
    parser = subparsers.add_parser("check", parents=[common], help="run the five output checks")
    parser.add_argument("document", help="the rendered .docx (or .pdf)")
    parser.set_defaults(func=cmd_check)


def _record_path(document: Path) -> Path:
    return document.parent / (document.stem + ".record.json")


def layout_dir(workspace, document: Path) -> Path:
    """Where the layout check renders a document's pages: ``.careerdocs/layout/`` in the
    workspace, mirroring the document's folder (``applications/<slug>``)."""
    root = Path(workspace).resolve()
    parent = document.resolve().parent
    try:
        relative = parent.relative_to(root)
    except ValueError:
        relative = Path(parent.name)
    return root / ".careerdocs" / "layout" / relative


def resume_bullets(document: Path) -> list[str]:
    """The bullets of every résumé rendered in the same folder as ``document``."""
    bullets: list[str] = []
    for record_path in sorted(document.parent.glob("*.record.json")):
        record = json.loads(record_path.read_text(encoding="utf-8"))
        plan_path = Path(record.get("content_plan") or "")
        if record.get("kind") != "resume" or not plan_path.is_file():
            continue
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        bullets += [unit["text"] for unit in plan["units"] if unit["kind"] == "bullet"]
    return bullets


def cmd_check(args) -> int:
    cfg = config_module.resolve_config(args.workspace)
    document = Path(args.document)
    record_path = _record_path(document)
    if not record_path.is_file():
        raise CareerDocsError(f"no output record at {record_path}", code="USAGE")
    record = json.loads(record_path.read_text(encoding="utf-8"))

    plan = json.loads(Path(record["content_plan"]).read_text(encoding="utf-8"))
    profile = load_provider(args.workspace, cfg).read()
    template = plan_module.load_template(args.workspace, cfg, record["kind"])

    pdf_path = None
    if document.suffix.lower() == ".pdf":
        pdf_path = document
    elif document.with_suffix(".pdf").is_file():
        pdf_path = document.with_suffix(".pdf")
    elif record.get("pdf") and Path(record["pdf"]).is_file():
        pdf_path = Path(record["pdf"])

    text = document_text(document)
    results = run_checks(text, pdf_path, plan, profile, template,
                         layout_dir=layout_dir(args.workspace, document) if pdf_path else None,
                         layout_name=document.stem, template_lines=record.get("template_lines", []),
                         resume_bullets=resume_bullets(document) if record["kind"] == "cover_letter" else ())

    apply_results(record, results)
    errors = validate_record(record)
    if errors:
        raise CareerDocsError("output record is invalid: " + "; ".join(errors))
    record_path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    exit_code = overall_exit_code(results)
    if args.json:
        print(json.dumps({"checks": record["checks"], "ok": exit_code == 0}))
    else:
        for name in CHECK_NAMES:
            print(f"{name}: {record['checks'][name]['status']} — {record['checks'][name]['details']}")
    return exit_code
