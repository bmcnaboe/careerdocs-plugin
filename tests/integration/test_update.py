"""US5 verification: updating qualifications propagates and reports staleness.

Runs the real CLI with Basic Memory authoritative (so a derived Markdown export exists)
over the example profile, then applies an update and checks the effects.
"""

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
from careerdocs.providers import load_provider  # noqa: E402
from careerdocs.providers.markdown import MarkdownProvider  # noqa: E402

CANDIDATES = ROOT / "tests" / "fixtures" / "candidates.json"
JD = ROOT / "examples" / "applicant" / "applications" / "example-role" / "job-description.md"
TEMPLATES = ROOT / "examples" / "applicant" / "templates"
SLUG = "example-role"
NOW = "2024-06-01T00:00:00Z"

UPDATE_CANDIDATES = {
    "candidates": [
        {
            "type": "experience", "ref": "globex",
            "provenance": {"source_id": "src_CCCCCCCCCCCCCCCCCCCCCCCCCC", "method": "statement", "recorded_at": NOW, "actor": "applicant", "excerpt": "I actually left Globex in September 2021."},
            "organization": "Globex Corporation", "title": "Engineering Manager",
            "start_date": "2018-03", "end_date": "2021-09",
        },
        {
            "type": "achievement", "parent_ref": "globex",
            "provenance": {"source_id": "src_CCCCCCCCCCCCCCCCCCCCCCCCCC", "method": "statement", "recorded_at": NOW, "actor": "applicant", "excerpt": "I launched the incident-response program."},
            "statement": "Launched the company-wide incident-response program.",
        },
    ]
}


def run(argv):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = cli.main(argv)
    return rc, buf.getvalue()


def run_json(argv):
    rc, out = run(argv)
    assert rc == 0, out
    return json.loads(out)


def bm_config(tmp_path):
    return {
        "version": "1",
        "providers": {
            "authoritative": "basic_memory",
            "markdown": {"path": "profile"},
            "basic_memory": {"vault_path": str(tmp_path / "vault"), "project": "test", "folder": "career"},
        },
    }


def setup(tmp_path):
    ws = str(tmp_path)
    (tmp_path / "careerdocs.json").write_text(json.dumps(bm_config(tmp_path)), encoding="utf-8")
    dest = tmp_path / "templates" / "resume"
    dest.mkdir(parents=True)
    shutil.copy(TEMPLATES / "resume" / "template.docx", dest / "template.docx")
    shutil.copy(TEMPLATES / "resume" / "template.json", dest / "template.json")

    d = run_json(["profile", "diff", str(CANDIDATES), "--workspace", ws, "--json"])
    run(["profile", "approve", d["diff_id"], "--workspace", ws])
    run(["profile", "apply", d["diff_id"], "--workspace", ws])

    app = tmp_path / "applications" / SLUG
    app.mkdir(parents=True)
    shutil.copy(JD, app / "job-description.md")
    run(["brief", str(app / "job-description.md"), "--role-slug", SLUG, "--workspace", ws])
    run(["map", "--role-slug", SLUG, "--workspace", ws])
    run(["plan", "--positioning", "builder", "--kind", "resume", "--role-slug", SLUG, "--workspace", ws])
    resume = run_json(["render", "--kind", "resume", "--role-slug", SLUG, "--workspace", ws, "--json"])
    return ws, app, resume


def apply_update(tmp_path, ws):
    ops_file = tmp_path / "update.json"
    ops_file.write_text(json.dumps(UPDATE_CANDIDATES), encoding="utf-8")
    diff = run_json(["profile", "diff", str(ops_file), "--flow", "update", "--subject", "globex", "--workspace", ws, "--json"])
    run(["profile", "approve", diff["diff_id"], "--workspace", ws])
    run(["profile", "apply", diff["diff_id"], "--workspace", ws])
    return diff


def test_new_fact_provenance(tmp_path):
    ws, app, _ = setup(tmp_path)
    before = {e["id"] for e in load_provider(tmp_path).read()["entities"]}
    apply_update(tmp_path, ws)
    profile = load_provider(tmp_path).read()

    new_achievement = next(
        e for e in profile["entities"]
        if e["type"] == "achievement" and e["statement"].startswith("Launched the company-wide")
    )
    assert new_achievement["id"] not in before  # fresh id
    assert any(p["method"] == "statement" and p["actor"] == "applicant" for p in new_achievement["provenance"])
    assert new_achievement["verification"] == "applicant_verified"


def test_exports_agree_and_stale(tmp_path):
    ws, app, resume = setup(tmp_path)
    apply_update(tmp_path, ws)

    # Authoritative Basic Memory notes and the derived Markdown export agree.
    note_ids = {e["id"] for e in load_provider(tmp_path).read()["entities"]}
    export_ids = {e["id"] for e in MarkdownProvider.at(tmp_path / "profile").read()["entities"]}
    assert note_ids == export_ids

    # The Globex end date actually changed.
    globex = next(e for e in load_provider(tmp_path).read()["entities"] if e.get("organization") == "Globex Corporation")
    assert globex["end_date"] == "2021-09"

    # The earlier résumé's output record is reported stale.
    status = run_json(["profile", "status", "--workspace", ws, "--json"])
    stale_docs = {item["document"] for item in status["stale_outputs"]}
    assert resume["record"] in {str(Path(d)) for d in stale_docs} or any(
        Path(resume["document"]).name in d for d in stale_docs
    )
    assert status["derived_export"]["fresh"] is True


def test_resume_pending_diff(tmp_path):
    ws, app, _ = setup(tmp_path)
    ops_file = tmp_path / "update.json"
    ops_file.write_text(json.dumps(UPDATE_CANDIDATES), encoding="utf-8")
    diff = run_json(["profile", "diff", str(ops_file), "--flow", "update", "--subject", "globex", "--workspace", ws, "--json"])

    # Interrupted before approval: resume shows the same pending diff, nothing to re-ask.
    resume = run_json(["state", "resume", "update", "globex", "--workspace", ws, "--json"])
    assert resume["pending_diff_id"] == diff["diff_id"]
    assert resume["unanswered"] == []
