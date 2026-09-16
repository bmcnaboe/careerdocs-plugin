"""Tests for the identity profile, its interview questions, and role alignment."""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "skills" / "careerdocs" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from careerdocs import brief, cli, identity, state  # noqa: E402
from careerdocs.config import default_config  # noqa: E402
from careerdocs.errors import CareerDocsError  # noqa: E402

EXAMPLE = ROOT / "examples" / "applicant" / "identity" / "identity.md"
CFG = default_config()
PARTIAL = '---\n{"version": "1", "values": [{"name": "Craft"}]}\n---\n'


def workspace_with_identity(tmp_path, text=None):
    cli.main(["config", "init", "--workspace", str(tmp_path)])
    path = tmp_path / "identity" / "identity.md"
    path.parent.mkdir()
    path.write_text(text if text is not None else EXAMPLE.read_text(encoding="utf-8"), encoding="utf-8")
    return str(tmp_path)


# --- the file ---


def test_example_identity_is_complete_and_valid():
    data, body = identity.parse_identity(EXAMPLE.read_text(encoding="utf-8"))
    assert identity.validate_identity(data) == []
    assert identity.missing_sections(data) == []
    assert "Stories" in body


def test_questions_only_for_missing_sections():
    data = {"version": "1", "values": [{"name": "Craft", "statement": "x"}], "working_style": "steady"}
    questions = identity.identity_questions(data)
    assert [q["field"] for q in questions] == ["personality", "motivations", "career_focus", "interests"]
    assert all(q["id"] == f"identity:{q['field']}" for q in questions)


def test_empty_sections_count_as_missing():
    data = {"version": "1", "values": [], "working_style": "  ", "career_focus": {"direction": ""}, "interests": []}
    assert identity.missing_sections(data) == [key for key, _ in identity.IDENTITY_SECTIONS]


def test_validate_rejects_bad_shapes():
    assert identity.validate_identity({"version": "1", "values": ["Craft"]})
    assert identity.validate_identity({"version": "1", "hobbies": []})
    assert identity.validate_identity({"version": "1", "career_focus": {"mission": "x"}})


def test_parse_requires_json_frontmatter():
    with pytest.raises(CareerDocsError):
        identity.parse_identity("# no frontmatter\n")
    with pytest.raises(CareerDocsError):
        identity.parse_identity("---\nnot json\n---\n")
    with pytest.raises(CareerDocsError):
        identity.parse_identity("---\n{}\n")


# --- alignment ---


def test_alignment_questions_offer_identity_options():
    data, _ = identity.parse_identity(EXAMPLE.read_text(encoding="utf-8"))
    role = {"organization": "Initech", "requirements": [], "recommended_positioning": "builder"}
    questions = identity.alignment_questions(role, data)
    assert [q["field"] for q in questions] == [key for key, _ in identity.ALIGNMENT_FIELDS]
    assert "Initech" in questions[0]["text"]
    by_field = {q["field"]: q for q in questions}
    assert by_field["values"]["options"] == [v["name"] for v in data["values"]]
    assert by_field["interests"]["options"] == data["interests"]
    assert by_field["focus"]["options"] == [data["career_focus"]["direction"]]
    assert "options" not in by_field["why"]


def test_alignment_questions_skip_answered_fields():
    role = {"alignment": {"why": "Because.", "values": ["Craft"], "focus": " "}, "requirements": [],
            "recommended_positioning": "builder"}
    questions = identity.alignment_questions(role, {})
    assert [q["field"] for q in questions] == ["interests", "focus", "through_line", "lead_story"]
    assert all("options" not in q for q in questions)


def test_brief_validate_accepts_alignment_and_rejects_unknown_keys():
    role = {"requirements": [], "recommended_positioning": "builder",
            "alignment": {"why": "x", "values": ["Craft"], "interests": [], "focus": "y",
                          "through_line": "z", "lead_story": "s", "notes": ""}}
    assert brief.validate_brief(role) == []
    role["alignment"]["mission"] = "invented"
    assert brief.validate_brief(role)


# --- CLI ---


def test_cli_show_reports_missing_file(tmp_path, capsys):
    cli.main(["config", "init", "--workspace", str(tmp_path)])
    capsys.readouterr()
    assert cli.main(["identity", "show", "--workspace", str(tmp_path), "--json"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["present"] is False and report["valid"] is False
    assert report["missing"] == [key for key, _ in identity.IDENTITY_SECTIONS]


def test_cli_show_and_validate_example(tmp_path, capsys):
    ws = workspace_with_identity(tmp_path)
    capsys.readouterr()
    assert cli.main(["identity", "show", "--workspace", ws, "--json"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["present"] and report["valid"] and report["missing"] == [] and report["has_stories"]
    assert cli.main(["identity", "validate", "--workspace", ws]) == 0


def test_cli_validate_absent_is_usage_error(tmp_path):
    cli.main(["config", "init", "--workspace", str(tmp_path)])
    assert cli.main(["identity", "validate", "--workspace", str(tmp_path)]) == 2


def test_cli_validate_invalid_exits_1(tmp_path):
    ws = workspace_with_identity(tmp_path, '---\n{"version": "1", "values": ["Craft"]}\n---\n')
    assert cli.main(["identity", "validate", "--workspace", ws]) == 1


def test_cli_questions_persist_to_state_and_carry_answers(tmp_path, capsys):
    ws = workspace_with_identity(tmp_path, PARTIAL)
    capsys.readouterr()
    argv = ["identity", "questions", "--flow", "onboard", "--subject", "default", "--workspace", ws, "--json"]
    assert cli.main(argv) == 0
    out = json.loads(capsys.readouterr().out)
    assert [q["field"] for q in out["questions"]] == ["personality", "motivations", "working_style", "career_focus", "interests"]
    assert all(q["answer"] is None for q in out["questions"])
    st = state.load_state(state.state_path(tmp_path, CFG, "onboard", "default"))
    assert {q["id"] for q in st["questions"]} == {q["id"] for q in out["questions"]}

    cli.main(["state", "answer", "onboard", "default", "--question", "identity:personality",
              "--answer", "Calm under pressure.", "--workspace", ws])
    capsys.readouterr()
    assert cli.main(argv) == 0
    out = json.loads(capsys.readouterr().out)
    answered = next(q for q in out["questions"] if q["field"] == "personality")
    assert answered["answer"] == "Calm under pressure."


def test_cli_questions_without_state_are_not_persisted(tmp_path, capsys):
    ws = workspace_with_identity(tmp_path, PARTIAL)
    capsys.readouterr()
    assert cli.main(["identity", "questions", "--workspace", ws, "--json"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert len(out["questions"]) == 5 and "answer" not in out["questions"][0]
    assert not (tmp_path / ".careerdocs").exists()


def test_cli_questions_flow_without_subject_is_usage_error(tmp_path):
    ws = workspace_with_identity(tmp_path, PARTIAL)
    assert cli.main(["identity", "questions", "--flow", "onboard", "--workspace", ws]) == 2


def test_brief_alignment_lists_open_questions_and_persists(tmp_path, capsys):
    ws = workspace_with_identity(tmp_path)
    app = tmp_path / "applications" / "initech-cto"
    app.mkdir(parents=True)
    role = {"organization": "Initech", "requirements": [], "recommended_positioning": "builder",
            "alignment": {"why": "Because."}}
    (app / "brief.json").write_text(json.dumps(role), encoding="utf-8")
    capsys.readouterr()
    assert cli.main(["brief", str(app / "brief.json"), "--alignment", "--flow", "apply", "--subject", "initech-cto",
                     "--workspace", ws, "--json"]) == 0
    out = json.loads(capsys.readouterr().out)
    fields = [q["field"] for q in out["questions"]]
    assert "why" not in fields and "through_line" in fields
    st = state.load_state(state.state_path(tmp_path, CFG, "apply", "initech-cto"))
    assert any(q["id"] == "alignment:through_line" for q in st["questions"])
    # The brief itself is untouched: the agent writes the alignment after the interview.
    assert json.loads((app / "brief.json").read_text(encoding="utf-8")) == role


def test_brief_alignment_without_identity_still_asks(tmp_path, capsys):
    cli.main(["config", "init", "--workspace", str(tmp_path)])
    app = tmp_path / "applications" / "initech-cto"
    app.mkdir(parents=True)
    (app / "brief.json").write_text(json.dumps({"requirements": [], "recommended_positioning": "builder"}), encoding="utf-8")
    capsys.readouterr()
    assert cli.main(["brief", str(app / "brief.json"), "--alignment", "--workspace", str(tmp_path), "--json"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert len(out["questions"]) == len(identity.ALIGNMENT_FIELDS)
    assert all("options" not in q for q in out["questions"])
