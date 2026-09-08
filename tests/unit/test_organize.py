"""Tests for the organize command, on a synthetic fixture tree."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "skills" / "careerdocs" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from careerdocs import cli, inventory, organize  # noqa: E402


def make_tree(tmp_path):
    (tmp_path / "resume_source_of_truth.md").write_text("truth", encoding="utf-8")
    (tmp_path / "jordan_resume.docx").write_text("resume", encoding="utf-8")
    (tmp_path / "job-applier-story-draft.md").write_text("draft", encoding="utf-8")
    (tmp_path / "jordan_resume.pdf").write_bytes(b"%PDF resume")
    (tmp_path / "output").mkdir()
    (tmp_path / "output" / "jordan_resume.pdf").write_bytes(b"%PDF resume")  # duplicate
    archive = tmp_path / "archive"
    archive.mkdir()
    (archive / "receipt.pdf").write_bytes(b"%PDF receipt")  # unrelated
    return tmp_path


def inventory_dict(tmp_path):
    return {"root": str(tmp_path), "files": inventory.build_inventory(tmp_path)}


def test_plan_moves_targets_destinations(tmp_path):
    make_tree(tmp_path)
    moves = dict(organize.plan_moves(inventory_dict(tmp_path)))
    assert moves["resume_source_of_truth.md"] == "sources/resume_source_of_truth.md"
    assert moves["jordan_resume.docx"] == "sources/jordan_resume.docx"
    assert moves["job-applier-story-draft.md"] == "archive/temporary/job-applier-story-draft.md"
    assert moves["output/jordan_resume.pdf"] == "archive/duplicates/output/jordan_resume.pdf"
    assert moves["archive/receipt.pdf"] == "archive/unrelated/archive/receipt.pdf"


def test_apply_moves_files_and_records(tmp_path):
    make_tree(tmp_path)
    inv = inventory_dict(tmp_path)
    organize.apply_moves(tmp_path, organize.plan_moves(inv))
    assert (tmp_path / "sources" / "jordan_resume.docx").exists()
    assert not (tmp_path / "jordan_resume.docx").exists()
    assert (tmp_path / "archive" / "temporary" / "job-applier-story-draft.md").exists()
    # Duplicate relocated, never deleted.
    assert (tmp_path / "archive" / "duplicates" / "output" / "jordan_resume.pdf").exists()
    moves = organize.read_moves(tmp_path)
    assert any(m["from"] == "jordan_resume.docx" for m in moves)


def test_dry_run_changes_nothing(tmp_path):
    make_tree(tmp_path)
    inv = inventory_dict(tmp_path)
    planned = organize.apply_moves(tmp_path, organize.plan_moves(inv), dry_run=True)
    assert planned
    assert (tmp_path / "jordan_resume.docx").exists()  # untouched
    assert not (tmp_path / "sources").exists()


def test_rollback_restores(tmp_path):
    make_tree(tmp_path)
    inv = inventory_dict(tmp_path)
    organize.apply_moves(tmp_path, organize.plan_moves(inv))
    organize.rollback(tmp_path)
    assert (tmp_path / "jordan_resume.docx").exists()
    assert (tmp_path / "output" / "jordan_resume.pdf").exists()
    assert not (tmp_path / "sources").exists()
    assert organize.read_moves(tmp_path) == []


def test_rollback_dry_run_is_clean(tmp_path):
    make_tree(tmp_path)
    inv = inventory_dict(tmp_path)
    organize.apply_moves(tmp_path, organize.plan_moves(inv))
    undone = organize.rollback(tmp_path, dry_run=True)
    assert undone  # would undo
    # Nothing actually moved back, and the log survives.
    assert (tmp_path / "sources" / "jordan_resume.docx").exists()
    assert organize.read_moves(tmp_path)


def test_cli_organize_apply_and_rollback(tmp_path, capsys):
    make_tree(tmp_path)
    inv_path = tmp_path / ".careerdocs" / "inventory.json"
    inventory.write_inventory(tmp_path, inventory.build_inventory(tmp_path), tmp_path / ".careerdocs")

    assert cli.main(["organize", "--inventory", str(inv_path), "--apply", "--json"]) == 0
    assert (tmp_path / "sources" / "jordan_resume.docx").exists()

    capsys.readouterr()
    assert cli.main(["organize", "--inventory", str(inv_path), "--rollback", "--dry-run", "--json"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["dry_run"] is True and report["rolled_back"] >= 1
    assert (tmp_path / "sources" / "jordan_resume.docx").exists()  # dry-run left it moved
