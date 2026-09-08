"""Tests for material question generation and answer conversion."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "skills" / "career-documents" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from careerdocs import ids, merge, questions, schema, state  # noqa: E402
from careerdocs.config import default_config  # noqa: E402

CANDIDATES = json.loads((ROOT / "tests" / "fixtures" / "candidates.json").read_text())
NOW = "2024-01-01T00:00:00Z"


def entity(entity_type, **extra):
    e = {
        "id": ids.new_id(entity_type), "type": entity_type, "visibility": "public",
        "verification": "imported",
        "provenance": [{"source_id": ids.new_source_id(), "method": "import", "recorded_at": NOW, "actor": "a"}],
        "created_at": NOW, "updated_at": NOW,
    }
    e.update(extra)
    return e


def test_conflict_question_generated():
    exp = entity("experience", organization="Acme", title="Eng", start_date="2020-01-01")
    exp["conflicts"] = [{"field": "end_date", "candidates": [
        {"value": "2022-01-01", "provenance": exp["provenance"][0]},
        {"value": "2023-01-01", "provenance": exp["provenance"][0]},
    ]}]
    qs = questions.generate_questions([exp])
    assert len(qs) == 1
    assert qs[0]["kind"] == "conflict" and qs[0]["field"] == "end_date"


def test_missing_start_date_question():
    exp = entity("experience", organization="Acme", title="Eng")
    qs = [q for q in questions.generate_questions([exp]) if q["kind"] == "date"]
    fields = {q["field"] for q in qs}
    assert "start_date" in fields and "end_date" in fields


def test_undecided_visibility_question():
    skill = entity("skill", name="Python")
    skill["visibility"] = None
    qs = [q for q in questions.generate_questions([skill]) if q["kind"] == "visibility"]
    assert len(qs) == 1


def test_no_visibility_question_when_public():
    skill = entity("skill", name="Python")  # visibility public
    assert [q for q in questions.generate_questions([skill]) if q["kind"] == "visibility"] == []


def test_example_yields_exactly_one_question():
    # The merged example profile has one material question: the Globex end-date conflict.
    ops = merge.build_operations({"entities": []}, CANDIDATES)
    proposed = [op["entity"] for op in ops if op["op"] == "add_entity"]
    qs = questions.generate_questions(proposed)
    assert len(qs) == 1
    assert qs[0]["kind"] == "conflict" and qs[0]["field"] == "end_date"


def test_answer_to_operation_conflict():
    q = {"kind": "conflict", "entity_id": "experience_x", "field": "end_date"}
    assert questions.answer_to_operation(q, "2021-08") == {
        "op": "resolve_conflict", "id": "experience_x", "field": "end_date", "value": "2021-08"}


def test_answer_to_operation_date_current():
    q = {"kind": "date", "entity_id": "experience_x", "field": "end_date"}
    op = questions.answer_to_operation(q, "current")
    assert op["op"] == "update_field" and op["to"] is None


def test_answer_to_operation_visibility():
    q = {"kind": "visibility", "entity_id": "skill_x", "field": "visibility"}
    assert questions.answer_to_operation(q, "private") == {
        "op": "set_visibility", "id": "skill_x", "visibility": "private"}


def test_no_question_repeats_after_resume(tmp_path):
    exp = entity("experience", organization="Acme", title="Eng", start_date="2020-01-01")
    exp["conflicts"] = [{"field": "end_date", "candidates": [
        {"value": "2022-01-01", "provenance": exp["provenance"][0]},
        {"value": "2023-01-01", "provenance": exp["provenance"][0]},
    ]}]
    cfg = default_config()
    path, wf = state.get_or_create(tmp_path, cfg, "onboard", "default")

    for q in questions.generate_questions([exp]):
        state.add_question(wf, q["id"], q["text"])
    state.answer_question(wf, "conflict:%s:end_date" % exp["id"], "2022-01-01")
    state.save_state(path, wf)

    # Resume: reload state and re-generate; nothing new is added.
    reloaded = state.load_state(path)
    added = [state.add_question(reloaded, q["id"], q["text"]) for q in questions.generate_questions([exp])]
    assert added == [False]  # the one question already existed
    assert len(reloaded["questions"]) == 1
    assert state.unanswered(reloaded) == []


def test_operations_from_answers_roundtrip():
    exp = entity("experience", organization="Acme", title="Eng", start_date="2020-01-01")
    exp["conflicts"] = [{"field": "end_date", "candidates": [
        {"value": "2022-01-01", "provenance": exp["provenance"][0]},
        {"value": "2023-01-01", "provenance": exp["provenance"][0]},
    ]}]
    qs = questions.generate_questions([exp])
    answered = {qs[0]["id"]: "2022-01-01"}
    ops = questions.operations_from_answers(qs, answered)
    assert ops == [{"op": "resolve_conflict", "id": exp["id"], "field": "end_date", "value": "2022-01-01"}]
