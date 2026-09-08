"""Resumable workflow state, one file per flow and subject.

State lives at ``<workflow.state_dir>/<flow>/<subject>.json`` and records the flow's step,
its append-only question list (each question has a stable id, so a resumed flow never asks
an answered question again), the pending diff, and the artifacts produced so far. Every
flow reads and updates this state, so an interrupted run continues from exactly where it
stopped.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import config as config_module
from . import util
from .errors import CareerDocsError

FLOWS = ("onboard", "update", "resume", "cover_letter")


def state_path(workspace, cfg: dict, flow: str, subject: str) -> Path:
    return Path(workspace) / cfg["workflow"]["state_dir"] / flow / f"{subject}.json"


def new_state(flow: str, subject: str) -> dict:
    now = util.now()
    return {
        "flow": flow,
        "subject": subject,
        "started_at": now,
        "updated_at": now,
        "step": "started",
        "questions": [],
        "pending_diff_id": None,
        "artifacts": {},
        "completed_at": None,
    }


def load_state(path: Path) -> dict | None:
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save_state(path: Path, state: dict) -> None:
    state["updated_at"] = util.now()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def get_or_create(workspace, cfg: dict, flow: str, subject: str) -> tuple[Path, dict]:
    path = state_path(workspace, cfg, flow, subject)
    state = load_state(path)
    if state is None:
        state = new_state(flow, subject)
        save_state(path, state)
    return path, state


def already_asked(state: dict, question_id: str) -> bool:
    return any(q["id"] == question_id for q in state["questions"])


def add_question(state: dict, question_id: str, text: str) -> bool:
    """Append a question unless one with this id was already asked. Returns whether added."""
    if already_asked(state, question_id):
        return False
    state["questions"].append({"id": question_id, "text": text, "answer": None, "answered_at": None})
    return True


def answer_question(state: dict, question_id: str, answer: str) -> None:
    for question in state["questions"]:
        if question["id"] == question_id:
            question["answer"] = answer
            question["answered_at"] = util.now()
            return
    raise CareerDocsError(f"no question {question_id!r} in this flow", code="USAGE")


def unanswered(state: dict) -> list[dict]:
    return [q for q in state["questions"] if q["answer"] is None]


def set_pending_diff(state: dict, diff_id: str | None) -> None:
    state["pending_diff_id"] = diff_id


def add_artifact(state: dict, name: str, path: str) -> None:
    state["artifacts"][name] = path


def set_step(state: dict, step: str) -> None:
    state["step"] = step


def complete(state: dict) -> None:
    state["step"] = "completed"
    state["completed_at"] = util.now()


# --- CLI ---


def register(subparsers, common: argparse.ArgumentParser) -> None:
    state_parser = subparsers.add_parser("state", help="inspect or update workflow state")
    actions = state_parser.add_subparsers(dest="state_command", metavar="<action>")
    actions.required = True

    show = actions.add_parser("show", parents=[common], help="print the workflow state")
    _flow_subject(show)
    show.set_defaults(func=cmd_show)

    answer = actions.add_parser("answer", parents=[common], help="record an answer")
    _flow_subject(answer)
    answer.add_argument("--question", required=True)
    answer.add_argument("--answer", required=True)
    answer.set_defaults(func=cmd_answer)

    resume = actions.add_parser("resume", parents=[common], help="show what remains to resume")
    _flow_subject(resume)
    resume.set_defaults(func=cmd_resume)


def _flow_subject(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("flow", choices=FLOWS)
    parser.add_argument("subject")


def _cfg(args) -> dict:
    return config_module.resolve_config(args.workspace)


def cmd_show(args) -> int:
    path = state_path(args.workspace, _cfg(args), args.flow, args.subject)
    state = load_state(path)
    if state is None:
        print(json.dumps({"exists": False}) if args.json else "no state for this flow/subject")
        return 0
    print(json.dumps(state, indent=2) if args.json else _human(state))
    return 0


def cmd_answer(args) -> int:
    path, state = get_or_create(args.workspace, _cfg(args), args.flow, args.subject)
    answer_question(state, args.question, args.answer)
    save_state(path, state)
    print(json.dumps({"answered": args.question}) if args.json else f"recorded answer to {args.question}")
    return 0


def cmd_resume(args) -> int:
    path = state_path(args.workspace, _cfg(args), args.flow, args.subject)
    state = load_state(path)
    if state is None:
        print(json.dumps({"exists": False}) if args.json else "nothing to resume")
        return 0
    pending = {
        "step": state["step"],
        "pending_diff_id": state["pending_diff_id"],
        "unanswered": unanswered(state),
        "artifacts": state["artifacts"],
    }
    if args.json:
        print(json.dumps(pending, indent=2))
    else:
        print(f"step: {pending['step']}")
        print(f"pending diff: {pending['pending_diff_id']}")
        if pending["unanswered"]:
            print("open questions:")
            for q in pending["unanswered"]:
                print(f"  - {q['id']}: {q['text']}")
        else:
            print("no open questions")
    return 0


def _human(state: dict) -> str:
    lines = [f"flow: {state['flow']}", f"subject: {state['subject']}", f"step: {state['step']}"]
    lines.append(f"questions: {len(state['questions'])} ({len(unanswered(state))} open)")
    lines.append(f"pending diff: {state['pending_diff_id']}")
    return "\n".join(lines)
