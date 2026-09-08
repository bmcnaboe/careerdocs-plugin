"""US2 verification: onboarding reconciles sources into one authoritative profile.

Drives the real careerdocs CLI over the example sources and the committed extracted
candidate set (standing in for the agent's extraction). No mocked providers.
"""

import contextlib
import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "skills" / "career-documents" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from careerdocs import cli, questions  # noqa: E402
from careerdocs.providers import load_provider  # noqa: E402
from careerdocs.providers.markdown import MarkdownProvider  # noqa: E402

SOURCES = ROOT / "examples" / "applicant" / "sources"
CANDIDATES = ROOT / "tests" / "fixtures" / "candidates.json"


def run(argv):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = cli.main(argv)
    return rc, buf.getvalue()


def run_json(argv):
    rc, out = run(argv)
    assert rc == 0, out
    return json.loads(out)


def onboard_diff(workspace):
    ws = str(workspace)
    run(["config", "init", "--workspace", ws])
    run(["profile", "import", str(SOURCES / "resume-a.docx"), str(SOURCES / "resume-b.pdf"), "--workspace", ws])
    return run_json([
        "profile", "diff", str(CANDIDATES),
        "--flow", "onboard", "--subject", "default", "--workspace", ws, "--json",
    ])


def globex_id(provider, diff_id):
    diff = provider.load_diff(diff_id)
    for op in diff["operations"]:
        if op["op"] == "add_entity" and op["entity"].get("organization") == "Globex Corporation":
            return op["entity"]["id"]
    raise AssertionError("Globex experience not in diff")


def test_conflict_one_question(tmp_path):
    out = onboard_diff(tmp_path)
    assert len(out["questions"]) == 1
    q = out["questions"][0]
    assert q["kind"] == "conflict" and q["field"] == "end_date"


def test_apply_single_entry(tmp_path):
    ws = str(tmp_path)
    out = onboard_diff(tmp_path)
    diff_id, question = out["diff_id"], out["questions"][0]
    provider = load_provider(tmp_path)
    gid = globex_id(provider, diff_id)

    # The applicant answers the conflict, then the add diff is approved and applied.
    run(["state", "answer", "onboard", "default", "--question", question["id"], "--answer", "2021-06", "--workspace", ws])
    run(["profile", "approve", diff_id, "--workspace", ws])
    run(["profile", "apply", diff_id, "--workspace", ws])

    # The recorded answer resolves the conflict in a follow-up diff.
    resolve = {"operations": [{"op": "resolve_conflict", "id": gid, "field": "end_date", "value": "2021-06"}]}
    ops_file = tmp_path / "resolve.json"
    ops_file.write_text(json.dumps(resolve), encoding="utf-8")
    d2 = run_json(["profile", "diff", str(ops_file), "--workspace", ws, "--json"])
    run(["profile", "approve", d2["diff_id"], "--workspace", ws])
    run(["profile", "apply", d2["diff_id"], "--workspace", ws])

    profile = load_provider(tmp_path).read()
    globex = [e for e in profile["entities"] if e.get("organization") == "Globex Corporation"]
    assert len(globex) == 1
    entity = globex[0]
    assert len(entity["provenance"]) == 2
    assert entity["verification"] == "applicant_verified"
    assert entity["end_date"] == "2021-06"
    assert entity["conflicts"][0]["resolution"]["value"] == "2021-06"


def test_resume_no_repeat(tmp_path):
    ws = str(tmp_path)
    out = onboard_diff(tmp_path)
    question = out["questions"][0]
    run(["state", "answer", "onboard", "default", "--question", question["id"], "--answer", "2021-06", "--workspace", ws])

    # Resume: no open questions remain.
    resume = run_json(["state", "resume", "onboard", "default", "--workspace", ws, "--json"])
    assert resume["unanswered"] == []

    # Re-generating questions from the same pending diff yields the same id, already answered.
    provider = load_provider(tmp_path)
    diff = provider.load_diff(out["diff_id"])
    proposed = [op["entity"] for op in diff["operations"] if op["op"] == "add_entity"]
    regenerated = questions.generate_questions(proposed)
    assert [q["id"] for q in regenerated] == [question["id"]]


def test_private_excluded(tmp_path):
    ws = str(tmp_path)
    out = onboard_diff(tmp_path)
    diff_id = out["diff_id"]
    run(["profile", "approve", diff_id, "--workspace", ws])
    run(["profile", "apply", diff_id, "--workspace", ws])

    provider = load_provider(tmp_path)
    python_skill = next(e for e in provider.read()["entities"] if e.get("name") == "Python")

    hide = {"operations": [{"op": "set_visibility", "id": python_skill["id"], "visibility": "private"}]}
    ops_file = tmp_path / "hide.json"
    ops_file.write_text(json.dumps(hide), encoding="utf-8")
    d2 = run_json(["profile", "diff", str(ops_file), "--workspace", ws, "--json"])
    run(["profile", "approve", d2["diff_id"], "--workspace", ws])
    run(["profile", "apply", d2["diff_id"], "--workspace", ws])

    # The private fact is in the authoritative profile but absent from the export.
    authoritative_names = {e.get("name") for e in provider.read()["entities"]}
    assert "Python" in authoritative_names
    export_dir = tmp_path / "derived"
    provider.export({"provider": "markdown", "path": str(export_dir)})
    exported_names = {e.get("name") for e in MarkdownProvider.at(export_dir).read()["entities"]}
    assert "Python" not in exported_names
