"""Tests for docxtpl rendering and the output record."""

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "skills" / "career-documents" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from careerdocs import brief, diff, mapping, merge, plan, render  # noqa: E402
from careerdocs.config import default_config  # noqa: E402
from careerdocs.providers import load_provider  # noqa: E402

CANDIDATES = json.loads((ROOT / "tests" / "fixtures" / "candidates.json").read_text())
JD = (ROOT / "examples" / "applicant" / "applications" / "example-role" / "job-description.md").read_text()
TEMPLATE_DIR = ROOT / "examples" / "applicant" / "templates" / "resume"
TEMPLATE_DOCX = TEMPLATE_DIR / "template.docx"
TEMPLATE_JSON = json.loads((TEMPLATE_DIR / "template.json").read_text())


def build_plan(tmp_path, positioning="builder"):
    provider = load_provider(tmp_path, default_config())
    ops = merge.build_operations(provider.read(), CANDIDATES)
    d = diff.make_diff(provider, ops)
    diff.approve(provider, d["diff_id"])
    diff.apply(provider, d["diff_id"], cfg=default_config(), workspace=tmp_path)
    b = brief.generate_brief(JD)
    m = mapping.generate_map(b, provider.read())
    return plan.generate_plan(m, provider.read(), TEMPLATE_JSON, positioning)


def read_docx_text(path):
    from docx import Document

    return "\n".join(p.text for p in Document(str(path)).paragraphs)


def test_render_produces_docx_with_plan_content(tmp_path):
    p = build_plan(tmp_path)
    out = tmp_path / "resume.docx"
    render.render_document(p, TEMPLATE_JSON, TEMPLATE_DOCX, out)
    text = read_docx_text(out)
    assert "Globex Corporation" in text
    assert "Cut deploy time" in text or "Grew the platform" in text
    assert "Python" in text


def test_render_omits_gap_requirement_content(tmp_path):
    p = build_plan(tmp_path)
    out = tmp_path / "resume.docx"
    render.render_document(p, TEMPLATE_JSON, TEMPLATE_DOCX, out)
    text = read_docx_text(out).lower()
    assert "fda" not in text
    assert "medical device" not in text


def test_stamped_output_naming():
    assert render.stamp().endswith("Z") and "T" in render.stamp()


def test_build_record_shape(tmp_path):
    p = build_plan(tmp_path)
    record = render.build_record(
        p, document=Path("out.docx"), kind="resume", positioning="builder",
        plan_path=Path("plan.json"), brief_path=Path("brief.json"), map_path=Path("map.json"),
        pdf_path=None, pdf_available=False,
    )
    expected_sources = {sid for u in p["units"] for sid in u["source_ids"]}
    assert set(record["source_ids"]) == expected_sources
    assert set(record["checks"]) == {"factual", "links_dates", "extraction", "pagination", "layout"}
    # Without a PDF, pagination and layout are skipped.
    assert record["checks"]["pagination"]["status"] == "skipped"
    assert record["checks"]["factual"]["status"] == "pending"
    assert record["stale"] is False


def test_cli_render_writes_docx_and_record(tmp_path, capsys):
    from careerdocs import cli

    ws = str(tmp_path)
    cli.main(["config", "init", "--workspace", ws])
    # Provision the template in the workspace.
    dest = tmp_path / "templates" / "resume"
    dest.mkdir(parents=True)
    shutil.copy(TEMPLATE_DOCX, dest / "template.docx")
    shutil.copy(TEMPLATE_DIR / "template.json", dest / "template.json")
    # Build the pipeline up to the plan.
    p = build_plan(tmp_path)
    app = tmp_path / "applications" / "example-role"
    app.mkdir(parents=True)
    (app / "plan.json").write_text(json.dumps(p), encoding="utf-8")

    capsys.readouterr()
    rc = cli.main(["render", "--kind", "resume", "--role-slug", "example-role", "--workspace", ws, "--json"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    doc = Path(out["document"])
    assert doc.exists() and doc.name.startswith("resume-")
    record = json.loads(Path(out["record"]).read_text())
    assert record["kind"] == "resume" and record["source_ids"]


COVER_DIR = ROOT / "examples" / "applicant" / "templates" / "cover-letter"
COVER_JSON = json.loads((COVER_DIR / "template.json").read_text())


def test_render_cover_letter(tmp_path):
    provider = load_provider(tmp_path, default_config())
    ops = merge.build_operations(provider.read(), CANDIDATES)
    d = diff.make_diff(provider, ops)
    diff.approve(provider, d["diff_id"])
    diff.apply(provider, d["diff_id"], cfg=default_config(), workspace=tmp_path)
    b = brief.generate_brief(JD)
    m = mapping.generate_map(b, provider.read())
    p = plan.generate_plan(m, provider.read(), COVER_JSON, "builder", brief=b)
    out = tmp_path / "letter.docx"
    render.render_document(p, COVER_JSON, COVER_DIR / "template.docx", out)
    text = read_docx_text(out)
    assert "Jordan Rivera" in text  # contact header
    # The body carries evidence content.
    assert "Globex Corporation" in text or "Kubernetes" in text or "platform" in text


def test_cli_render_pdf_branch(tmp_path):
    from careerdocs import cli

    ws = str(tmp_path)
    cli.main(["config", "init", "--workspace", ws])
    dest = tmp_path / "templates" / "resume"
    dest.mkdir(parents=True)
    shutil.copy(TEMPLATE_DOCX, dest / "template.docx")
    shutil.copy(TEMPLATE_DIR / "template.json", dest / "template.json")
    p = build_plan(tmp_path)
    app = tmp_path / "applications" / "example-role"
    app.mkdir(parents=True)
    (app / "plan.json").write_text(json.dumps(p), encoding="utf-8")

    rc = cli.main(["render", "--kind", "resume", "--role-slug", "example-role", "--pdf", "--workspace", ws])
    assert rc == 0
    outputs = list((app / "outputs").glob("resume-*.docx"))
    assert outputs
    if shutil.which("soffice"):
        assert list((app / "outputs").glob("resume-*.pdf"))
