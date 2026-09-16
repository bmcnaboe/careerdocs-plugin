"""The identity profile and role alignment: who the applicant is beyond the facts.

The identity profile (``identity.path``, default ``identity/identity.md``) is an
applicant-owned Markdown file with a JSON frontmatter block, like the voice profile. Its
durable sections — values, personality, motivations, working style — change rarely; its
current sections — career focus and interests — are revisited and refined per application.
The Markdown body holds the stories the applicant tells about themselves. The cover-letter
flow drafts from all of it so a letter has a through-line of the applicant's own rather
than a walk through the requirements. It is never a source of qualifications: every fact a
document states still traces to a profile entity.

Per application, the brief's ``alignment`` records how one role connects to the identity:
why this role, which values and interests it engages, the focus it serves, the through-line
the letter is organized around, and the story that carries it.

Both are captured by interview, one question at a time. ``identity questions`` and
``brief --alignment`` emit only the questions whose answers are still missing, each with a
stable id, and persist them to workflow state when a flow and subject are given, so a
resumed flow never asks an answered question twice. The agent drafts the file or the
``alignment`` block from the answers and writes it only after the applicant's yes.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import config as config_module
from . import schema
from . import state as state_module
from .errors import CareerDocsError

IDENTITY_SECTIONS = (
    ("values", "What do you care about most in your work? Name two to four values, each with a "
               "sentence on what it looks like in practice."),
    ("personality", "How do colleagues experience you? Two or three traits, each with a short example."),
    ("motivations", "What kind of work energizes you, and what drains you?"),
    ("working_style", "How do you like to work: alone or with others, fast or careful, structured "
                      "or improvised?"),
    ("career_focus", "Where is your career heading? The direction, the roles and settings you want "
                     "next, and the ones to avoid."),
    ("interests", "Which problems, domains, or technologies are you drawn to right now?"),
)
DURABLE_SECTIONS = ("values", "personality", "motivations", "working_style")
CURRENT_SECTIONS = ("career_focus", "interests")

ALIGNMENT_FIELDS = (
    ("why", "Why this role at {organization}? Say it the way you would to a friend."),
    ("values", "Which of your values does this role engage?"),
    ("interests", "Which of your interests does it serve, or what new one does it open?"),
    ("focus", "Which part of your career focus does it advance?"),
    ("through_line", "In one sentence, what is the one idea the letter should be organized around?"),
    ("lead_story", "Which story or piece of evidence carries that idea best?"),
)


def identity_path(workspace, cfg: dict) -> Path:
    return Path(workspace) / cfg["identity"]["path"]


def parse_identity(text: str) -> tuple[dict, str]:
    """Split an identity file into its JSON frontmatter and Markdown body."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise CareerDocsError("identity profile has no frontmatter block", code="USAGE")
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        raise CareerDocsError("identity profile frontmatter is not closed", code="USAGE")
    raw = "\n".join(lines[1:end]).strip()
    try:
        data = json.loads(raw) if raw else {}
    except json.JSONDecodeError as exc:
        raise CareerDocsError(f"identity frontmatter is not valid JSON: {exc}", code="USAGE") from exc
    if not isinstance(data, dict):
        raise CareerDocsError("identity frontmatter must be a JSON object", code="USAGE")
    return data, "\n".join(lines[end + 1:]).strip()


def section_present(data: dict, key: str) -> bool:
    value = data.get(key)
    if key == "career_focus":
        return isinstance(value, dict) and bool((value.get("direction") or "").strip())
    if key == "working_style":
        return isinstance(value, str) and bool(value.strip())
    return isinstance(value, list) and len(value) > 0


def missing_sections(data: dict) -> list[str]:
    return [key for key, _ in IDENTITY_SECTIONS if not section_present(data, key)]


def validate_identity(data: dict) -> list[str]:
    return schema.validate_against("identity", data)


def load_identity(workspace, cfg: dict) -> dict:
    """The identity profile as a report: whether it exists, its frontmatter and body, its
    schema errors, and the sections it still lacks."""
    path = identity_path(workspace, cfg)
    report = {"path": cfg["identity"]["path"], "present": path.is_file(), "frontmatter": {},
              "body": "", "errors": [], "missing": [key for key, _ in IDENTITY_SECTIONS]}
    if not report["present"]:
        return report
    data, body = parse_identity(path.read_text(encoding="utf-8"))
    report.update(frontmatter=data, body=body, errors=validate_identity(data), missing=missing_sections(data))
    return report


def identity_questions(data: dict) -> list[dict]:
    """One interview question per section the identity profile still lacks."""
    return [
        {"id": f"identity:{key}", "kind": "identity", "field": key, "text": text}
        for key, text in IDENTITY_SECTIONS
        if not section_present(data, key)
    ]


def _alignment_options(key: str, identity: dict) -> list[str]:
    if key == "values":
        return [v["name"] for v in identity.get("values") or [] if isinstance(v, dict) and v.get("name")]
    if key == "interests":
        return [i for i in identity.get("interests") or [] if isinstance(i, str)]
    if key == "focus":
        direction = (identity.get("career_focus") or {}).get("direction")
        return [direction] if direction else []
    return []


def alignment_questions(brief: dict, identity: dict) -> list[dict]:
    """One question per alignment field the brief still lacks, offering the identity's
    own values, interests, and direction as options where they apply."""
    alignment = brief.get("alignment") or {}
    organization = brief.get("organization") or "this organization"
    questions: list[dict] = []
    for key, text in ALIGNMENT_FIELDS:
        value = alignment.get(key)
        if (value.strip() if isinstance(value, str) else value):
            continue
        question = {"id": f"alignment:{key}", "kind": "alignment", "field": key,
                    "text": text.format(organization=organization)}
        options = _alignment_options(key, identity)
        if options:
            question["options"] = options
        questions.append(question)
    return questions


def attach_state(workspace, cfg: dict, flow: str | None, subject: str | None, questions: list[dict]) -> list[dict]:
    """Persist the questions under a workflow (so a resumed flow sees them) and annotate
    each with the answer already recorded, if any. Without a flow nothing is persisted."""
    if flow is None and subject is None:
        return questions
    if flow is None or subject is None:
        raise CareerDocsError("--flow and --subject go together", code="USAGE")
    path, workflow = state_module.get_or_create(workspace, cfg, flow, subject)
    for question in questions:
        state_module.add_question(workflow, question["id"], question["text"])
    state_module.save_state(path, workflow)
    answered = {q["id"]: q["answer"] for q in workflow["questions"]}
    return [{**question, "answer": answered.get(question["id"])} for question in questions]


def print_questions(questions: list[dict], *, as_json: bool, label: str) -> None:
    if as_json:
        print(json.dumps({"questions": questions}))
        return
    if not questions:
        print(f"no open {label} questions")
        return
    for question in questions:
        status = "answered" if question.get("answer") else "open"
        print(f"[{status}] {question['id']}: {question['text']}")
        if question.get("options"):
            print("    options: " + "; ".join(question["options"]))
        if question.get("answer"):
            print(f"    answer: {question['answer']}")


# --- CLI ---


def register(subparsers, common: argparse.ArgumentParser) -> None:
    parser = subparsers.add_parser("identity", help="inspect the identity profile or list its open questions")
    actions = parser.add_subparsers(dest="identity_command", metavar="<action>")
    actions.required = True

    show = actions.add_parser("show", parents=[common], help="report the identity profile and the sections it lacks")
    show.set_defaults(func=cmd_show)

    validate = actions.add_parser("validate", parents=[common], help="validate the identity profile's frontmatter")
    validate.set_defaults(func=cmd_validate)

    questions = actions.add_parser(
        "questions", parents=[common], help="list the interview questions for the sections still missing"
    )
    questions.add_argument("--flow", choices=state_module.FLOWS, help="persist the questions under this flow")
    questions.add_argument("--subject", help="the workflow subject to persist under")
    questions.set_defaults(func=cmd_questions)


def cmd_show(args) -> int:
    report = load_identity(args.workspace, config_module.resolve_config(args.workspace))
    data = report["frontmatter"]
    summary = {
        "path": report["path"],
        "present": report["present"],
        "valid": report["present"] and not report["errors"],
        "errors": report["errors"],
        "sections": {key: section_present(data, key) for key, _ in IDENTITY_SECTIONS},
        "missing": report["missing"],
        "has_stories": bool(report["body"]),
    }
    if args.json:
        print(json.dumps(summary, ensure_ascii=False))
        return 0
    print(f"identity ({summary['path']}): {'present' if summary['present'] else 'missing'}")
    if summary["present"]:
        print("valid" if summary["valid"] else "INVALID: " + "; ".join(summary["errors"]))
        print("missing sections: " + (", ".join(summary["missing"]) or "none"))
        print(f"stories in the body: {'yes' if summary['has_stories'] else 'no'}")
    return 0


def cmd_validate(args) -> int:
    cfg = config_module.resolve_config(args.workspace)
    report = load_identity(args.workspace, cfg)
    if not report["present"]:
        raise CareerDocsError(f"no identity profile at {identity_path(args.workspace, cfg)}", code="USAGE")
    for message in report["errors"]:
        print(message)
    if report["errors"]:
        raise CareerDocsError("identity profile is invalid", exit_code=1)
    print(json.dumps({"valid": True, "missing": report["missing"]}) if args.json else "identity profile is valid")
    return 0


def cmd_questions(args) -> int:
    cfg = config_module.resolve_config(args.workspace)
    report = load_identity(args.workspace, cfg)
    questions = attach_state(args.workspace, cfg, args.flow, args.subject, identity_questions(report["frontmatter"]))
    print_questions(questions, as_json=args.json, label="identity")
    return 0
