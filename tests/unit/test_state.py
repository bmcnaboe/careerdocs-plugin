"""Tests for workflow state and the state subcommands."""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "skills" / "careerdocs" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from careerdocs import cli, state  # noqa: E402
from careerdocs.config import default_config  # noqa: E402
from careerdocs.errors import CareerDocsError  # noqa: E402

CFG = default_config()


def test_get_or_create_persists(tmp_path):
    path, st = state.get_or_create(tmp_path, CFG, "onboard", "default")
    assert path.exists()
    assert st["flow"] == "onboard" and st["step"] == "started"


def test_add_question_is_idempotent_by_id(tmp_path):
    _, st = state.get_or_create(tmp_path, CFG, "onboard", "default")
    assert state.add_question(st, "q1", "First?") is True
    assert state.add_question(st, "q1", "First (again)?") is False
    assert len(st["questions"]) == 1


def test_answer_and_unanswered(tmp_path):
    _, st = state.get_or_create(tmp_path, CFG, "onboard", "default")
    state.add_question(st, "q1", "First?")
    state.add_question(st, "q2", "Second?")
    state.answer_question(st, "q1", "yes")
    assert [q["id"] for q in state.unanswered(st)] == ["q2"]


def test_answer_unknown_question_raises(tmp_path):
    _, st = state.get_or_create(tmp_path, CFG, "onboard", "default")
    with pytest.raises(CareerDocsError):
        state.answer_question(st, "nope", "x")


def test_question_not_reasked_after_reload(tmp_path):
    path, st = state.get_or_create(tmp_path, CFG, "onboard", "default")
    state.add_question(st, "q1", "First?")
    state.answer_question(st, "q1", "yes")
    state.save_state(path, st)
    reloaded = state.load_state(path)
    # Re-generating the same question id must not re-add it.
    assert state.add_question(reloaded, "q1", "First?") is False
    assert state.unanswered(reloaded) == []


def test_pending_diff_and_artifacts(tmp_path):
    path, st = state.get_or_create(tmp_path, CFG, "update", "role-x")
    state.set_pending_diff(st, "diff_123")
    state.add_artifact(st, "brief", "applications/x/brief.json")
    state.complete(st)
    state.save_state(path, st)
    reloaded = state.load_state(path)
    assert reloaded["pending_diff_id"] == "diff_123"
    assert reloaded["artifacts"]["brief"].endswith("brief.json")
    assert reloaded["step"] == "completed" and reloaded["completed_at"]


# --- CLI ---


def test_cli_show_missing(tmp_path, capsys):
    cli.main(["config", "init", "--workspace", str(tmp_path)])
    capsys.readouterr()  # drop the config-init output
    assert cli.main(["state", "show", "onboard", "default", "--workspace", str(tmp_path), "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["exists"] is False


def test_cli_answer_then_resume(tmp_path, capsys):
    cli.main(["config", "init", "--workspace", str(tmp_path)])
    cfg = default_config()
    path, st = state.get_or_create(tmp_path, cfg, "onboard", "default")
    state.add_question(st, "q1", "Which end date?")
    state.save_state(path, st)

    assert cli.main([
        "state", "answer", "onboard", "default",
        "--question", "q1", "--answer", "2022", "--workspace", str(tmp_path),
    ]) == 0
    capsys.readouterr()  # drop the answer-confirmation output
    assert cli.main(["state", "resume", "onboard", "default", "--workspace", str(tmp_path), "--json"]) == 0
    resume = json.loads(capsys.readouterr().out)
    assert resume["unanswered"] == []
