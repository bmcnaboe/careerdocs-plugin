"""US2-5 verification: onboarding with Basic Memory authoritative.

Runs the real CLI onboarding sequence with ``authoritative: basic_memory`` against a
temporary vault, then checks the notes and the derived Markdown export hold the same ids
and the export is labeled derived.
"""

import contextlib
import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "skills" / "careerdocs" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from careerdocs import cli  # noqa: E402
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


def write_bm_config(workspace):
    config = {
        "version": "1",
        "providers": {
            "authoritative": "basic_memory",
            "markdown": {"path": "profile"},
            "basic_memory": {"vault_path": str(workspace / "vault"), "project": "test", "folder": "career"},
        },
    }
    (workspace / "careerdocs.json").write_text(json.dumps(config), encoding="utf-8")


def test_basic_memory_onboarding_ids_and_derived_export(tmp_path):
    ws = str(tmp_path)
    write_bm_config(tmp_path)
    assert cli.main(["config", "validate", "--workspace", ws]) == 0

    run(["profile", "import", str(SOURCES / "resume-a.docx"), str(SOURCES / "resume-b.pdf"), "--workspace", ws])
    diff = run_json(["profile", "diff", str(CANDIDATES), "--flow", "onboard", "--subject", "default", "--workspace", ws, "--json"])
    run(["profile", "approve", diff["diff_id"], "--workspace", ws])
    run(["profile", "apply", diff["diff_id"], "--workspace", ws])

    # Authoritative provider is Basic Memory: entities are notes in the vault.
    bm = load_provider(tmp_path)
    note_ids = {e["id"] for e in bm.read()["entities"]}
    assert note_ids
    # A note file exists with a permalink under the career folder.
    contact_id = next(e["id"] for e in bm.read()["entities"] if e["type"] == "contact")
    note = (tmp_path / "vault" / "career" / "contact" / f"{contact_id}.md").read_text()
    assert '"permalink": "career/contact/' in note

    # The derived Markdown export holds the same ids and is labeled derived.
    export = MarkdownProvider.at(tmp_path / "profile").read()
    assert export["derived"] is True
    assert {e["id"] for e in export["entities"]} == note_ids


def test_derived_export_omits_private(tmp_path):
    ws = str(tmp_path)
    write_bm_config(tmp_path)
    run(["profile", "import", str(SOURCES / "resume-a.docx"), "--workspace", ws])
    diff = run_json(["profile", "diff", str(CANDIDATES), "--flow", "onboard", "--subject", "default", "--workspace", ws, "--json"])
    run(["profile", "approve", diff["diff_id"], "--workspace", ws])
    run(["profile", "apply", diff["diff_id"], "--workspace", ws])

    bm = load_provider(tmp_path)
    python_skill = next(e for e in bm.read()["entities"] if e.get("name") == "Python")
    hide = {"operations": [{"op": "set_visibility", "id": python_skill["id"], "visibility": "private"}]}
    ops_file = tmp_path / "hide.json"
    ops_file.write_text(json.dumps(hide), encoding="utf-8")
    d2 = run_json(["profile", "diff", str(ops_file), "--workspace", ws, "--json"])
    run(["profile", "approve", d2["diff_id"], "--workspace", ws])
    run(["profile", "apply", d2["diff_id"], "--workspace", ws])

    # Private in the authoritative notes, absent from the refreshed derived export.
    assert any(e.get("name") == "Python" for e in load_provider(tmp_path).read()["entities"])
    export = MarkdownProvider.at(tmp_path / "profile").read()
    assert "Python" not in {e.get("name") for e in export["entities"]}
