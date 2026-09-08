"""US4 verification: a complementary cover letter, via the real CLI."""

import contextlib
import io
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "skills" / "careerdocs" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from careerdocs import cli  # noqa: E402
from careerdocs.checks import factual  # noqa: E402
from careerdocs.config import default_config  # noqa: E402
from careerdocs.providers import load_provider  # noqa: E402

CANDIDATES = ROOT / "tests" / "fixtures" / "candidates.json"
JD = ROOT / "examples" / "applicant" / "applications" / "example-role" / "job-description.md"
TEMPLATES = ROOT / "examples" / "applicant" / "templates"
COVER_JSON = json.loads((TEMPLATES / "cover-letter" / "template.json").read_text())
SLUG = "example-role"


def run(argv):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = cli.main(argv)
    return rc, buf.getvalue()


def run_json(argv):
    rc, out = run(argv)
    assert rc == 0, out
    return json.loads(out)


def résumé_then_letter(tmp_path):
    ws = str(tmp_path)
    run(["config", "init", "--workspace", ws])
    for kind in ("resume", "cover-letter"):
        dest = tmp_path / "templates" / kind
        dest.mkdir(parents=True)
        shutil.copy(TEMPLATES / kind / "template.docx", dest / "template.docx")
        shutil.copy(TEMPLATES / kind / "template.json", dest / "template.json")
    d = run_json(["profile", "diff", str(CANDIDATES), "--workspace", ws, "--json"])
    run(["profile", "approve", d["diff_id"], "--workspace", ws])
    run(["profile", "apply", d["diff_id"], "--workspace", ws])
    app = tmp_path / "applications" / SLUG
    app.mkdir(parents=True)
    shutil.copy(JD, app / "job-description.md")

    # Résumé first: brief, map, plan, render.
    run(["brief", str(app / "job-description.md"), "--role-slug", SLUG, "--workspace", ws])
    run(["map", "--role-slug", SLUG, "--workspace", ws])
    run(["plan", "--positioning", "builder", "--kind", "resume", "--role-slug", SLUG, "--workspace", ws])
    resume = run_json(["render", "--kind", "resume", "--role-slug", SLUG, "--workspace", ws, "--json"])
    resume_plan = json.loads((app / "plan.json").read_text())

    return ws, app, resume, resume_plan


def docx_text(path):
    from docx import Document

    return "\n".join(p.text for p in Document(str(path)).paragraphs)


def test_reuses_brief_and_map(tmp_path):
    ws, app, _, _ = résumé_then_letter(tmp_path)
    brief_before = (app / "brief.json").read_text()
    map_before = (app / "map.json").read_text()

    # The letter plan reuses brief and map without re-running them.
    run(["plan", "--positioning", "builder", "--kind", "cover_letter", "--role-slug", SLUG, "--workspace", ws])

    assert (app / "brief.json").read_text() == brief_before
    assert (app / "map.json").read_text() == map_before
    # No new workflow questions were created for the letter.
    state_dir = tmp_path / ".careerdocs" / "state" / "cover_letter"
    assert not state_dir.exists()


def test_checks_and_budget(tmp_path):
    ws, app, _, _ = résumé_then_letter(tmp_path)
    run(["plan", "--positioning", "builder", "--kind", "cover_letter", "--role-slug", SLUG, "--workspace", ws])
    letter_plan = json.loads((app / "plan.json").read_text())
    # Fits the one-page budget (page_budget 1 * units_per_page 6).
    assert len(letter_plan["units"]) <= COVER_JSON["page_budget"] * COVER_JSON["units_per_page"]

    rendered = run_json(["render", "--kind", "cover_letter", "--pdf", "--role-slug", SLUG, "--workspace", ws, "--json"])
    result = run_json(["check", rendered["document"], "--workspace", ws, "--json"])
    assert result["checks"]["factual"]["status"] == "pass"
    for name in ("extraction", "pagination", "layout"):
        assert result["checks"][name]["status"] in ("pass", "skipped")

    # No gap requirement is claimed.
    text = docx_text(rendered["document"]).lower()
    assert "fda" not in text and "medical device" not in text


def test_no_verbatim_bullets(tmp_path):
    ws, app, _, resume_plan = résumé_then_letter(tmp_path)
    run(["plan", "--positioning", "builder", "--kind", "cover_letter", "--role-slug", SLUG, "--workspace", ws])
    letter_plan = json.loads((app / "plan.json").read_text())
    rendered = run_json(["render", "--kind", "cover_letter", "--role-slug", SLUG, "--workspace", ws, "--json"])
    letter_text = docx_text(rendered["document"])

    resume_bullets = [u["text"] for u in resume_plan["units"] if u["kind"] == "bullet"]
    assert resume_bullets  # the résumé has achievement bullets
    assert factual.verbatim_bullet_check(letter_text, resume_bullets)["status"] == "pass"

    # Every letter claim still traces to a cited entity.
    profile = load_provider(tmp_path).read()
    result = factual.check(letter_text, letter_plan, profile, allowlist=COVER_JSON["allowlist"])
    assert result["status"] == "pass", result["details"]
