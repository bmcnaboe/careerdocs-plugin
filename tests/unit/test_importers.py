"""Tests for the source importers and `profile import`, over the example sources."""

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "skills" / "careerdocs" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from careerdocs import cli, ids, importers  # noqa: E402
from careerdocs.providers import load_provider  # noqa: E402

SOURCES = ROOT / "examples" / "applicant" / "sources"


def test_detect_kind():
    assert importers.detect_kind(SOURCES / "resume-a.docx") == "resume_docx"
    assert importers.detect_kind(SOURCES / "resume-b.pdf") == "resume_pdf"
    assert importers.detect_kind(SOURCES / "network-export.csv") == "network_export"
    assert importers.detect_kind(SOURCES / "voice-note.md") == "note"


def test_docx_text_blocks():
    out = importers.import_source(SOURCES / "resume-a.docx", ids.new_source_id())
    joined = "\n".join(out["text_blocks"])
    assert "Globex Corporation" in joined
    assert "June 2021" in joined
    assert out["candidates"] == []


def test_pdf_text_blocks():
    out = importers.import_source(SOURCES / "resume-b.pdf", ids.new_source_id())
    joined = "\n".join(out["text_blocks"])
    assert "August 2021" in joined
    assert out["candidates"] == []


def test_csv_yields_experience_candidates():
    out = importers.import_source(SOURCES / "network-export.csv", ids.new_source_id())
    orgs = {c["organization"] for c in out["candidates"]}
    assert {"Globex Corporation", "Initech"} <= orgs
    globex = next(c for c in out["candidates"] if c["organization"] == "Globex Corporation")
    assert globex["type"] == "experience"
    assert globex["start_date"] == "2018-03"
    assert globex["provenance"]["method"] == "extraction"


def test_note_text_blocks():
    out = importers.import_source(SOURCES / "voice-note.md", ids.new_source_id())
    assert out["text_blocks"]
    assert out["candidates"] == []


def test_cli_import_registers_sources_with_sha256(tmp_path, capsys):
    cli.main(["config", "init", "--workspace", str(tmp_path)])
    capsys.readouterr()
    rc = cli.main([
        "profile", "import",
        str(SOURCES / "resume-a.docx"), str(SOURCES / "resume-b.pdf"),
        "--workspace", str(tmp_path), "--json",
    ])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert len(payload["sources"]) == 2

    # Sources are registered in the provider's ledger with a correct sha256.
    provider = load_provider(tmp_path)
    ledger = {s["location"]: s for s in provider.read_sources()}
    assert len(ledger) == 2
    for source in payload["sources"]:
        assert source["sha256"] == hashlib.sha256(
            (SOURCES / Path(source["location"]).name).read_bytes()
        ).hexdigest()


def test_cli_import_writes_out_file(tmp_path):
    cli.main(["config", "init", "--workspace", str(tmp_path)])
    out_file = tmp_path / "imports.json"
    rc = cli.main([
        "profile", "import", str(SOURCES / "network-export.csv"),
        "--workspace", str(tmp_path), "--out", str(out_file),
    ])
    assert rc == 0
    payload = json.loads(out_file.read_text())
    assert payload["imports"][0]["candidates"]
