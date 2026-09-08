"""Tests for the workspace inventory classifier, on a synthetic fixture tree."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "skills" / "careerdocs" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from careerdocs import cli, inventory  # noqa: E402


def make_tree(tmp_path):
    (tmp_path / "resume_source_of_truth.md").write_text("truth", encoding="utf-8")
    (tmp_path / "jordan_resume_2026.docx").write_text("resume docx", encoding="utf-8")
    (tmp_path / "held_sleep_brand_guidelines.md").write_text("brand", encoding="utf-8")
    (tmp_path / "linkedin_export.csv").write_text("Company,Title\n", encoding="utf-8")
    (tmp_path / "job-applier-plugin-story-draft.md").write_text("draft", encoding="utf-8")
    (tmp_path / ".DS_Store").write_text("ds", encoding="utf-8")

    # A root PDF and an identical copy under output/pdf -> the copy is a duplicate.
    (tmp_path / "jordan_resume_builder.pdf").write_bytes(b"%PDF-1.4 builder resume")
    (tmp_path / "output" / "pdf").mkdir(parents=True)
    (tmp_path / "output" / "pdf" / "jordan_resume_builder.pdf").write_bytes(b"%PDF-1.4 builder resume")

    archive = tmp_path / "archive"
    archive.mkdir()
    (archive / "old_resume_2018.docx").write_text("old resume", encoding="utf-8")
    (archive / "tax_return_2020.pdf").write_bytes(b"%PDF-1.4 taxes")
    return tmp_path


def index(entries):
    return {e["path"]: e for e in entries}


def test_classifications(tmp_path):
    make_tree(tmp_path)
    entries = inventory.build_inventory(tmp_path)
    by_path = index(entries)
    assert by_path["resume_source_of_truth.md"]["category"] == "authoritative_data"
    assert by_path["jordan_resume_2026.docx"]["category"] == "source_evidence"
    assert by_path["held_sleep_brand_guidelines.md"]["category"] == "template_voice"
    assert by_path["linkedin_export.csv"]["category"] == "source_evidence"
    assert by_path["job-applier-plugin-story-draft.md"]["category"] == "temporary"
    assert by_path[".DS_Store"]["category"] == "temporary"
    assert by_path["archive/old_resume_2018.docx"]["category"] == "historical_record"
    assert by_path["archive/tax_return_2020.pdf"]["category"] == "unrelated"


def test_output_copy_is_duplicate(tmp_path):
    make_tree(tmp_path)
    by_path = index(inventory.build_inventory(tmp_path))
    root_pdf = by_path["jordan_resume_builder.pdf"]
    copy_pdf = by_path["output/pdf/jordan_resume_builder.pdf"]
    assert root_pdf["category"] == "source_evidence"
    assert copy_pdf["category"] == "duplicate"
    assert copy_pdf["duplicate_of"] == "jordan_resume_builder.pdf"


def test_every_file_has_a_destination(tmp_path):
    make_tree(tmp_path)
    for entry in inventory.build_inventory(tmp_path):
        assert entry["destination"]


def test_writes_json_and_md(tmp_path):
    make_tree(tmp_path)
    entries = inventory.build_inventory(tmp_path)
    out = tmp_path / ".careerdocs"
    json_path, md_path = inventory.write_inventory(tmp_path, entries, out)
    assert json_path.exists() and md_path.exists()
    data = json.loads(json_path.read_text())
    assert data["counts"]["source_evidence"] >= 2
    assert "| Path |" in md_path.read_text()


def test_cli_inventory(tmp_path, capsys):
    make_tree(tmp_path)
    assert cli.main(["inventory", str(tmp_path), "--json"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert Path(out["inventory"]).exists()
    assert out["counts"]["duplicate"] == 1


def test_inventory_skips_its_own_output(tmp_path):
    make_tree(tmp_path)
    # Running twice must not classify the previous inventory.json.
    inventory.write_inventory(tmp_path, inventory.build_inventory(tmp_path), tmp_path / ".careerdocs")
    entries = inventory.build_inventory(tmp_path)
    assert not any(".careerdocs" in e["path"] for e in entries)