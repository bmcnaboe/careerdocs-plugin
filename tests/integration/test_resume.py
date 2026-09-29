"""US3 verification: a tailored résumé from brief through checks, via the real CLI."""

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

CANDIDATES = ROOT / "tests" / "fixtures" / "candidates.json"
JD = ROOT / "examples" / "applicant" / "applications" / "example-role" / "job-description.md"
TEMPLATE_DIR = ROOT / "examples" / "applicant" / "templates" / "resume"
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


def build_workspace(tmp_path):
    ws = str(tmp_path)
    run(["config", "init", "--workspace", ws])
    dest = tmp_path / "templates" / "resume"
    dest.mkdir(parents=True)
    shutil.copy(TEMPLATE_DIR / "template.docx", dest / "template.docx")
    shutil.copy(TEMPLATE_DIR / "template.json", dest / "template.json")
    # Build the profile from the extracted candidates.
    d = run_json(["profile", "diff", str(CANDIDATES), "--workspace", ws, "--json"])
    run(["profile", "approve", d["diff_id"], "--workspace", ws])
    run(["profile", "apply", d["diff_id"], "--workspace", ws])
    app = tmp_path / "applications" / SLUG
    app.mkdir(parents=True)
    shutil.copy(JD, app / "job-description.md")
    return ws, app


def run_pipeline(tmp_path, positioning="builder", page_budget=None):
    ws, app = build_workspace(tmp_path)
    run(["brief", str(app / "job-description.md"), "--role-slug", SLUG, "--workspace", ws])
    run(["map", "--role-slug", SLUG, "--workspace", ws])
    plan_args = ["plan", "--positioning", positioning, "--kind", "resume", "--role-slug", SLUG, "--workspace", ws]
    if page_budget is not None:
        plan_args += ["--page-budget", str(page_budget)]
    run(plan_args)
    rendered = run_json(["render", "--kind", "resume", "--pdf", "--role-slug", SLUG, "--workspace", ws, "--json"])
    return ws, app, rendered


def docx_text(path):
    from docx import Document

    return "\n".join(p.text for p in Document(str(path)).paragraphs)


def test_pipeline_artifacts(tmp_path):
    ws, app, rendered = run_pipeline(tmp_path)
    brief_p = app / "brief.json"
    map_p = app / "map.json"
    plan_p = app / "plan.resume.json"
    document = Path(rendered["document"])
    for artifact in (brief_p, map_p, plan_p, document):
        assert artifact.exists()
    # Produced in order.
    assert brief_p.stat().st_mtime <= map_p.stat().st_mtime <= plan_p.stat().st_mtime <= document.stat().st_mtime


def test_gap_never_claimed(tmp_path):
    ws, app, rendered = run_pipeline(tmp_path)
    mapping = json.loads((app / "map.json").read_text())
    # The FDA requirement is a gap.
    assert any(e["classification"] == "gap" for e in mapping)
    text = docx_text(rendered["document"]).lower()
    assert "fda" not in text and "medical device" not in text


def test_positioning_inverts(tmp_path):
    # One workspace, one profile: only the positioning changes between the two plans.
    ws, app = build_workspace(tmp_path)
    run(["brief", str(app / "job-description.md"), "--role-slug", SLUG, "--workspace", ws])
    run(["map", "--role-slug", SLUG, "--workspace", ws])

    run(["plan", "--positioning", "builder", "--kind", "resume", "--role-slug", SLUG, "--workspace", ws])
    builder_plan = json.loads((app / "plan.resume.json").read_text())
    run(["plan", "--positioning", "executive", "--kind", "resume", "--role-slug", SLUG, "--workspace", ws])
    executive_plan = json.loads((app / "plan.resume.json").read_text())

    def first_skill(plan):
        return next(u["source_ids"][0] for u in plan["units"] if u["section_id"] == "skills")

    def skill_ids(plan):
        return {sid for u in plan["units"] if u["section_id"] == "skills" for sid in u["source_ids"]}

    # Same facts, inverted emphasis: the leading skill differs, the set is identical.
    assert first_skill(builder_plan) != first_skill(executive_plan)
    assert skill_ids(builder_plan) == skill_ids(executive_plan)


def test_five_checks(tmp_path):
    ws, app, rendered = run_pipeline(tmp_path, page_budget=1)
    result = run_json(["check", rendered["document"], "--workspace", ws, "--json"])
    checks = result["checks"]
    assert set(checks) == {"factual", "links_dates", "extraction", "pagination", "layout"}
    assert checks["factual"]["status"] == "pass"
    assert checks["links_dates"]["status"] in ("pass", "skipped")
    for name in ("extraction", "pagination", "layout"):
        assert checks[name]["status"] in ("pass", "skipped")
    assert result["ok"] is True


def test_default_two_page_target_rejects_short_resume(tmp_path):
    ws, app, rendered = run_pipeline(tmp_path)
    assert json.loads((app / "plan.resume.json").read_text())["page_budget"] == 2
    # Supply a known one-page PDF so this check also runs without LibreOffice.
    shutil.copyfile(ROOT / "tests" / "fixtures" / "rendered" / "example-resume.pdf",
                    Path(rendered["document"]).with_suffix(".pdf"))
    rc, out = run(["check", rendered["document"], "--workspace", ws, "--json"])
    assert rc == 1
    assert json.loads(out)["checks"]["pagination"]["status"] == "fail"


def test_budget_cuts_reported(tmp_path):
    ws, app = build_workspace(tmp_path)
    # Tighten the template so the experience section cannot fit everything.
    tpl = json.loads((tmp_path / "templates" / "resume" / "template.json").read_text())
    for section in tpl["sections"]:
        if section["id"] == "experience":
            section["max_items"] = 1
    (tmp_path / "templates" / "resume" / "template.json").write_text(json.dumps(tpl), encoding="utf-8")

    run(["brief", str(app / "job-description.md"), "--role-slug", SLUG, "--workspace", ws])
    run(["map", "--role-slug", SLUG, "--workspace", ws])
    out = run_json(["plan", "--positioning", "builder", "--kind", "resume", "--role-slug", SLUG, "--workspace", ws, "--json"])
    assert out["cuts"] >= 1
    plan = json.loads((app / "plan.resume.json").read_text())
    assert plan["cuts"]


def test_a_tailored_plan_starts_from_the_positioning_baseline(tmp_path):
    ws, app = build_workspace(tmp_path)
    run(["plan", "--baseline", "--positioning", "builder", "--workspace", ws])
    baseline = json.loads((tmp_path / "baselines" / "builder" / "plan.resume.json").read_text())
    baseline["units"][1]["text"] = baseline["units"][1]["text"] + " (as the baseline wrote it)"
    (tmp_path / "baselines" / "builder" / "plan.resume.json").write_text(json.dumps(baseline))
    run(["brief", str(app / "job-description.md"), "--role-slug", SLUG, "--workspace", ws])
    run(["map", "--role-slug", SLUG, "--workspace", ws])

    out = run_json(["plan", "--kind", "resume", "--role-slug", SLUG, "--workspace", ws, "--json"])
    tailored = json.loads((app / "plan.resume.json").read_text())
    assert out["baseline"] == "baselines/builder/plan.resume.json"
    assert tailored["units"][1]["text"].endswith("(as the baseline wrote it)")
    assert set(tailored["tailoring"]) == {"add", "compress"}

    # --fresh selects afresh and records no baseline.
    run(["plan", "--kind", "resume", "--role-slug", SLUG, "--fresh", "--workspace", ws])
    assert "baseline" not in json.loads((app / "plan.resume.json").read_text())


def test_the_approach_names_the_baseline_to_start_from(tmp_path):
    ws, app = build_workspace(tmp_path)
    run(["plan", "--baseline", "--positioning", "builder", "--workspace", ws])
    run(["brief", str(app / "job-description.md"), "--role-slug", SLUG, "--workspace", ws])
    run(["map", "--role-slug", SLUG, "--workspace", ws])
    brief_path = app / "brief.json"

    def plan_with(baseline):
        brief = json.loads(brief_path.read_text())
        brief["approach"] = {**brief.get("approach", {}), "baseline": baseline}
        brief_path.write_text(json.dumps(brief))
        return run(["plan", "--kind", "resume", "--role-slug", SLUG, "--workspace", ws, "--json"])

    rc, out = plan_with("builder")
    assert rc == 0 and json.loads(out)["baseline"] == "baselines/builder/plan.resume.json"
    assert json.loads(out)["positioning"] == "builder"
    rc, out = plan_with("none")
    assert rc == 0 and json.loads(out)["baseline"] is None
    rc, _ = plan_with("executive")  # chosen, but never built
    assert rc == 2


def test_a_baseline_plan_is_replaced_only_on_request(tmp_path):
    ws, _ = build_workspace(tmp_path)
    assert run(["plan", "--baseline", "--positioning", "builder", "--workspace", ws])[0] == 0
    baseline = tmp_path / "baselines" / "builder" / "plan.resume.json"
    baseline.write_text(baseline.read_text().replace("Globex", "Globex (edited)"))
    edited = baseline.read_text()
    assert run(["plan", "--baseline", "--positioning", "builder", "--workspace", ws])[0] == 2
    assert baseline.read_text() == edited
    assert run(["plan", "--baseline", "--positioning", "builder", "--replace", "--workspace", ws])[0] == 0
    assert baseline.read_text() != edited
