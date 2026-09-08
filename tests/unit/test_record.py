"""Tests for the output record and the check runner."""

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "skills" / "career-documents" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from careerdocs import brief, cli, diff, mapping, merge, plan, record, render  # noqa: E402
from careerdocs.config import default_config  # noqa: E402
from careerdocs.providers import load_provider  # noqa: E402

CANDIDATES = json.loads((ROOT / "tests" / "fixtures" / "candidates.json").read_text())
JD = (ROOT / "examples" / "applicant" / "applications" / "example-role" / "job-description.md").read_text()
TEMPLATE_DIR = ROOT / "examples" / "applicant" / "templates" / "resume"
TEMPLATE_JSON = json.loads((TEMPLATE_DIR / "template.json").read_text())
EXAMPLE_PDF = ROOT / "tests" / "fixtures" / "rendered" / "example-resume.pdf"


def build(tmp_path):
    provider = load_provider(tmp_path, default_config())
    ops = merge.build_operations(provider.read(), CANDIDATES)
    d = diff.make_diff(provider, ops)
    diff.approve(provider, d["diff_id"])
    diff.apply(provider, d["diff_id"], cfg=default_config(), workspace=tmp_path)
    b = brief.generate_brief(JD)
    m = mapping.generate_map(b, provider.read())
    p = plan.generate_plan(m, provider.read(), TEMPLATE_JSON, "builder")
    out = tmp_path / "resume.docx"
    render.render_document(p, TEMPLATE_JSON, TEMPLATE_DIR / "template.docx", out)
    text = "\n".join(par.text for par in __import__("docx").Document(str(out)).paragraphs)
    return p, provider.read(), text


def test_run_checks_all_pass_with_pdf(tmp_path):
    p, profile, text = build(tmp_path)
    results = record.run_checks(text, EXAMPLE_PDF, p, profile, TEMPLATE_JSON, layout_dir=tmp_path / "layout")
    assert set(results) == set(record.CHECK_NAMES)
    assert all(r["status"] == "pass" for r in results.values()), results
    assert record.overall_exit_code(results) == 0


def test_run_checks_without_pdf_skips_pdf_checks(tmp_path):
    p, profile, text = build(tmp_path)
    results = record.run_checks(text, None, p, profile, TEMPLATE_JSON)
    assert results["factual"]["status"] == "pass"
    for name in ("extraction", "pagination", "layout"):
        assert results[name]["status"] == "skipped"
    assert record.overall_exit_code(results) == 0


def test_overall_exit_code_fails_on_check_fail():
    results = {n: {"status": "pass", "details": ""} for n in record.CHECK_NAMES}
    results["factual"] = {"status": "fail", "details": "boom"}
    assert record.overall_exit_code(results) == 1


def test_record_validates(tmp_path):
    p, profile, _ = build(tmp_path)
    rec = render.build_record(
        p, document=Path("out.docx"), kind="resume", positioning="builder",
        plan_path=Path("plan.json"), brief_path=None, map_path=None, pdf_path=None, pdf_available=False,
    )
    results = {n: {"status": "pass", "details": "ok"} for n in record.CHECK_NAMES}
    record.apply_results(rec, results)
    assert record.validate_record(rec) == []


def test_invalid_record_detected():
    bad = {"document": "x"}  # missing everything
    assert record.validate_record(bad)


def test_cli_render_then_check(tmp_path, capsys):
    ws = str(tmp_path)
    cli.main(["config", "init", "--workspace", ws])
    dest = tmp_path / "templates" / "resume"
    dest.mkdir(parents=True)
    shutil.copy(TEMPLATE_DIR / "template.docx", dest / "template.docx")
    shutil.copy(TEMPLATE_DIR / "template.json", dest / "template.json")
    p, _, _ = build(tmp_path)
    app = tmp_path / "applications" / "example-role"
    app.mkdir(parents=True)
    (app / "plan.json").write_text(json.dumps(p), encoding="utf-8")

    capsys.readouterr()
    assert cli.main(["render", "--kind", "resume", "--role-slug", "example-role", "--pdf", "--workspace", ws, "--json"]) == 0
    rendered = json.loads(capsys.readouterr().out)
    document = rendered["document"]

    capsys.readouterr()
    rc = cli.main(["check", document, "--workspace", ws, "--json"])
    result = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert result["ok"] is True
    assert result["checks"]["factual"]["status"] == "pass"
    if shutil.which("soffice"):
        assert result["checks"]["pagination"]["status"] == "pass"
