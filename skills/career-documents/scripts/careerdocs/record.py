"""Run the five checks and record the verdict.

``check <document>`` extracts the document text, runs the factual, links/dates,
extraction, pagination, and layout checks (the last three need a PDF; skipped with a
reason when there is none), updates the output record, and exits 1 if any check failed.
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
               *, layout_dir: Path | None = None, layout_name: str = "layout") -> dict:
    allowlist = template.get("allowlist", []) if template else []
    results = {
        "factual": factual.check(text, plan, profile, allowlist=allowlist),
        "links_dates": links_dates.check(text),
    }
    if pdf_path is not None:
        results["extraction"] = extraction.check(pdf_path)
        results["pagination"] = pagination_check(pdf_path, plan)
        results["layout"] = layout.check(pdf_path, out_dir=layout_dir, name=layout_name)
    else:
        for name in ("extraction", "pagination", "layout"):
            results[name] = {"status": "skipped", "details": "no PDF (soffice not available)"}
    return results


def pagination_check(pdf_path: Path, plan: dict) -> dict:
    from .checks import pagination

    return pagination.check(pdf_path, plan.get("page_budget", 2))


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
    layout_dir = document.parent / "layout"
    results = run_checks(text, pdf_path, plan, profile, template,
                         layout_dir=layout_dir if pdf_path else None, layout_name=document.stem)

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
