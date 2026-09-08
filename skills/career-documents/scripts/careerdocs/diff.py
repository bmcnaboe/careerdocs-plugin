"""Proposed changes: build, render, approve, and apply a ProfileDiff.

Every change to the authoritative profile is a reviewable ProfileDiff — a ``base_hash``
(the hash of the profile it was proposed against), a list of operations, and a rendered
Markdown summary. Nothing mutates the profile until ``apply``, and ``apply`` refuses
unless a recorded approval's hash matches the diff and the diff's ``base_hash`` still
matches the current profile. Applying refreshes any derived export.

Operations (each an object with an ``op`` discriminator):

* ``add_entity`` ``{entity}``
* ``update_field`` ``{id, field, from, to, provenance?}``
* ``resolve_conflict`` ``{id, field, value, by?}``
* ``set_visibility`` ``{id, visibility}``
* ``retire_entity`` ``{id, reason}``
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from . import config as config_module
from . import ids, schema, util
from .errors import ApprovalMissing, BaseHashMismatch, CareerDocsError, ConfigError
from .providers import load_provider
from .providers.base import hash_profile

OP_KINDS = {"add_entity", "update_field", "resolve_conflict", "set_visibility", "retire_entity"}


def diff_hash(diff: dict) -> str:
    payload = {
        "diff_id": diff["diff_id"],
        "base_hash": diff["base_hash"],
        "operations": diff["operations"],
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def render_diff_markdown(diff: dict, profile: dict) -> str:
    by_id = {e["id"]: e for e in profile["entities"]}
    lines = [f"# Proposed profile changes ({diff['diff_id']})", ""]
    if not diff["operations"]:
        lines.append("_No changes._")
        return "\n".join(lines) + "\n"
    for op in diff["operations"]:
        kind = op["op"]
        if kind == "add_entity":
            entity = op["entity"]
            label = entity.get("name") or entity.get("title") or entity.get("statement") or entity["id"]
            lines.append(f"- **Add {entity['type']}**: {label}")
        elif kind == "update_field":
            lines.append(f"- **Update** {op['id']} `{op['field']}`: {op.get('from')!r} → {op['to']!r}")
        elif kind == "resolve_conflict":
            lines.append(f"- **Resolve conflict** {op['id']} `{op['field']}` → {op['value']!r}")
        elif kind == "set_visibility":
            lines.append(f"- **Set visibility** {op['id']} → {op['visibility']}")
        elif kind == "retire_entity":
            existing = by_id.get(op["id"], {})
            label = existing.get("name") or existing.get("title") or op["id"]
            lines.append(f"- **Retire** {label} ({op.get('reason', 'no reason given')})")
    return "\n".join(lines) + "\n"


def make_diff(provider, operations: list[dict], *, base_hash: str | None = None) -> dict:
    for op in operations:
        if op.get("op") not in OP_KINDS:
            raise CareerDocsError(f"unknown diff operation {op.get('op')!r}")
    profile = provider.read()
    diff = {
        "diff_id": ids.new_diff_id(),
        "base_hash": base_hash if base_hash is not None else hash_profile(profile),
        "operations": operations,
    }
    diff["summary_md"] = render_diff_markdown(diff, profile)
    provider.store_diff(diff)
    return diff


def changed_entity_ids(diff: dict) -> set[str]:
    changed: set[str] = set()
    for op in diff["operations"]:
        if op["op"] == "add_entity":
            changed.add(op["entity"]["id"])
        elif "id" in op:
            changed.add(op["id"])
    return changed


def apply_operations(profile: dict, operations: list[dict]) -> dict:
    entities = {e["id"]: dict(e) for e in profile["entities"]}
    order = [e["id"] for e in profile["entities"]]
    now = util.now()

    for op in operations:
        kind = op["op"]
        if kind == "add_entity":
            entity = dict(op["entity"])
            if entity["id"] not in entities:
                order.append(entity["id"])
            entities[entity["id"]] = entity
        elif kind == "update_field":
            entity = entities[op["id"]]
            entity[op["field"]] = op["to"]
            if op.get("provenance"):
                entity.setdefault("provenance", []).append(op["provenance"])
            entity["updated_at"] = now
        elif kind == "resolve_conflict":
            entity = entities[op["id"]]
            entity[op["field"]] = op["value"]
            for conflict in entity.get("conflicts", []):
                if conflict["field"] == op["field"] and not conflict.get("resolution"):
                    conflict["resolution"] = {
                        "value": op["value"],
                        "resolved_at": now,
                        "by": op.get("by", "applicant"),
                    }
            entity["verification"] = "applicant_verified"
            entity["updated_at"] = now
        elif kind == "set_visibility":
            entity = entities[op["id"]]
            entity["visibility"] = op["visibility"]
            entity["updated_at"] = now
        elif kind == "retire_entity":
            entities.pop(op["id"], None)
            if op["id"] in order:
                order.remove(op["id"])
        else:
            raise CareerDocsError(f"unknown diff operation {kind!r}")

    new_entities = [entities[i] for i in order if i in entities]
    return {**profile, "entities": new_entities, "updated_at": now}


def approve(provider, diff_id: str, *, scope="all", by="applicant", note=None, document=None) -> dict:
    diff = provider.load_diff(diff_id)
    approval = {
        "diff_id": diff_id,
        "diff_hash": diff_hash(diff),
        "approved_at": util.now(),
        "by": by,
        "scope": scope,
    }
    if note:
        approval["note"] = note
    if document:
        approval["document"] = document
    provider.append_approval(approval)
    return approval


def refresh_exports(provider, cfg: dict, workspace) -> list[str]:
    """Refresh the derived export (the non-authoritative copy), if one is implied."""
    if cfg is None:
        return []
    authoritative = cfg["providers"]["authoritative"]
    if authoritative == "basic_memory":
        path = Path(workspace) / cfg["providers"]["markdown"]["path"]
        provider.export({"provider": "markdown", "path": str(path)})
        return [str(path)]
    return []


def apply(provider, diff_id: str, *, cfg: dict | None = None, workspace=None) -> dict:
    diff = provider.load_diff(diff_id)
    approval = provider.find_approval(diff_id)
    if approval is None:
        raise ApprovalMissing(f"no approval recorded for {diff_id}; approve it first")
    if approval.get("diff_hash") != diff_hash(diff):
        raise ApprovalMissing(f"the approval for {diff_id} does not match the current diff")

    current = provider.read()
    if diff["base_hash"] != hash_profile(current):
        raise BaseHashMismatch(
            f"{diff_id} was proposed against a different profile state; re-propose it"
        )

    new_profile = apply_operations(current, diff["operations"])
    schema.assert_valid_profile(new_profile)
    new_hash = provider.write(new_profile)
    exported = refresh_exports(provider, cfg, workspace)
    stale = mark_stale_outputs(workspace, cfg, changed_entity_ids(diff))
    return {"applied": diff_id, "hash": new_hash, "exported": exported, "stale_outputs": stale}


def _output_record_paths(workspace, cfg: dict) -> list[Path]:
    base = Path(workspace)
    paths: list[Path] = []
    apps = base / cfg["outputs"]["applications_dir"]
    if apps.is_dir():
        paths += apps.glob("*/outputs/*.record.json")
    baselines = base / cfg["outputs"]["baselines_dir"]
    if baselines.is_dir():
        paths += baselines.glob("*/*.record.json")
    return sorted(paths)


def mark_stale_outputs(workspace, cfg: dict | None, changed_ids: set[str]) -> list[str]:
    """Mark any output record whose source ids include a changed entity as stale."""
    if cfg is None or workspace is None or not changed_ids:
        return []
    stale: list[str] = []
    for path in _output_record_paths(workspace, cfg):
        record = json.loads(path.read_text(encoding="utf-8"))
        if record.get("stale"):
            continue
        overlap = set(record.get("source_ids", [])) & changed_ids
        if overlap:
            record["stale"] = True
            record["stale_reason"] = f"source entities changed: {sorted(overlap)}"
            path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            stale.append(record.get("document", str(path)))
    return stale


def derived_freshness(provider, cfg: dict, workspace) -> dict:
    if cfg["providers"]["authoritative"] != "basic_memory":
        return {"applicable": False}
    from .providers.markdown import MarkdownProvider
    from .visibility import filter_visible

    md_path = Path(workspace) / cfg["providers"]["markdown"]["path"]
    if not (md_path / "profile.md").exists():
        return {"applicable": True, "present": False, "fresh": False}
    expected = {e["id"] for e in filter_visible(provider.read(), for_export=True)["entities"]}
    actual = {e["id"] for e in MarkdownProvider.at(md_path).read()["entities"]}
    return {"applicable": True, "present": True, "fresh": expected == actual, "path": str(md_path)}


# --- CLI ---


def register(subparsers, common: argparse.ArgumentParser) -> None:
    profile = subparsers.add_parser("profile", help="manage the authoritative profile")
    actions = profile.add_subparsers(dest="profile_command", metavar="<action>")
    actions.required = True

    validate = actions.add_parser("validate", parents=[common], help="validate the profile")
    validate.set_defaults(func=cmd_validate)

    import_parser = actions.add_parser(
        "import", parents=[common], help="register sources and emit candidate skeletons"
    )
    import_parser.add_argument("sources", nargs="+")
    import_parser.add_argument("--out", help="also write the emitted JSON to this file")
    import_parser.set_defaults(func=cmd_import)

    diff_parser = actions.add_parser("diff", parents=[common], help="build a ProfileDiff")
    diff_parser.add_argument("input", help="JSON file of diff operations or extracted candidates")
    diff_parser.add_argument("--flow", choices=["onboard", "update", "resume", "cover_letter"])
    diff_parser.add_argument("--subject", help="workflow subject to persist questions under")
    diff_parser.set_defaults(func=cmd_diff)

    approve_parser = actions.add_parser("approve", parents=[common], help="record approval of a diff")
    approve_parser.add_argument("diff_id")
    approve_parser.add_argument("--note")
    approve_parser.add_argument("--scope", default="all")
    approve_parser.add_argument("--document", help="grant restricted entities into this document")
    approve_parser.set_defaults(func=cmd_approve)

    apply_parser = actions.add_parser("apply", parents=[common], help="apply an approved diff")
    apply_parser.add_argument("diff_id")
    apply_parser.set_defaults(func=cmd_apply)

    export_parser = actions.add_parser("export", parents=[common], help="write a derived copy")
    export_parser.add_argument("--to", choices=["markdown", "basic_memory"], required=True)
    export_parser.set_defaults(func=cmd_export)

    status_parser = actions.add_parser("status", parents=[common], help="report stale outputs and export freshness")
    status_parser.set_defaults(func=cmd_status)


def _provider(args):
    cfg = config_module.resolve_config(args.workspace)
    return load_provider(args.workspace, cfg), cfg


def cmd_validate(args) -> int:
    provider, _ = _provider(args)
    try:
        provider.read()
    except CareerDocsError as exc:
        print(json.dumps({"valid": False, "error": str(exc)}) if args.json else f"invalid: {exc}")
        return 1
    print(json.dumps({"valid": True}) if args.json else "profile is valid")
    return 0


def cmd_import(args) -> int:
    from . import importers

    provider, _ = _provider(args)
    registered: list[dict] = []
    results: list[dict] = []
    workspace_root = Path(args.workspace).resolve()
    for source in args.sources:
        path = Path(source)
        sha = hashlib.sha256(path.read_bytes()).hexdigest()
        kind = importers.detect_kind(path)
        if kind is None:
            raise CareerDocsError(f"unsupported source type {path.suffix!r}", code="USAGE")
        try:
            location = str(path.resolve().relative_to(workspace_root))
        except ValueError:
            location = str(path)
        source_record = {
            "source_id": ids.new_source_id(),
            "kind": kind,
            "location": location,
            "sha256": sha,
            "captured_at": util.now(),
        }
        provider.append_source(source_record)
        registered.append(source_record)
        extracted = importers.import_source(path, source_record["source_id"])
        results.append({"source_id": source_record["source_id"], "kind": kind, "location": location, **extracted})

    payload = {"sources": registered, "imports": results}
    if args.out:
        Path(args.out).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    if args.json:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        for result in results:
            print(
                f"{result['kind']}: {result['location']} — "
                f"{len(result['text_blocks'])} text block(s), {len(result['candidates'])} candidate(s)"
            )
    return 0


def cmd_diff(args) -> int:
    provider, cfg = _provider(args)
    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    from_candidates = isinstance(payload, dict) and "candidates" in payload
    if from_candidates:
        from . import merge

        operations = merge.build_operations(provider.read(), payload)
    else:
        operations = payload["operations"] if isinstance(payload, dict) else payload
    diff = make_diff(provider, operations)

    generated: list[dict] = []
    if from_candidates:
        from . import questions as questions_module

        proposed = [op["entity"] for op in operations if op["op"] == "add_entity"]
        generated = questions_module.generate_questions(proposed)
        if args.flow and args.subject:
            _persist_questions(args, cfg, diff["diff_id"], generated)

    if args.json:
        print(json.dumps({
            "diff_id": diff["diff_id"],
            "base_hash": diff["base_hash"],
            "questions": generated,
        }))
    else:
        print(diff["summary_md"])
        print(f"diff id: {diff['diff_id']}")
        for question in generated:
            print(f"  ? {question['id']}: {question['text']}")
    return 0


def _persist_questions(args, cfg: dict, diff_id: str, generated: list[dict]) -> None:
    from . import state as state_module

    path, workflow = state_module.get_or_create(args.workspace, cfg, args.flow, args.subject)
    for question in generated:
        state_module.add_question(workflow, question["id"], question["text"])
    state_module.set_pending_diff(workflow, diff_id)
    state_module.set_step(workflow, "awaiting_answers" if generated else "awaiting_approval")
    state_module.save_state(path, workflow)


def cmd_approve(args) -> int:
    provider, _ = _provider(args)
    approval = approve(
        provider, args.diff_id, scope=args.scope, note=args.note, document=args.document
    )
    print(json.dumps(approval) if args.json else f"approved {args.diff_id}")
    return 0


def cmd_apply(args) -> int:
    provider, cfg = _provider(args)
    result = apply(provider, args.diff_id, cfg=cfg, workspace=args.workspace)
    if args.json:
        print(json.dumps(result))
    else:
        print(f"applied {args.diff_id}")
        if result["exported"]:
            print("refreshed derived export: " + ", ".join(result["exported"]))
    return 0


def cmd_status(args) -> int:
    provider, cfg = _provider(args)
    stale = []
    for path in _output_record_paths(args.workspace, cfg):
        record = json.loads(path.read_text(encoding="utf-8"))
        if record.get("stale"):
            stale.append({"document": record.get("document", str(path)), "reason": record.get("stale_reason")})
    report = {"stale_outputs": stale, "derived_export": derived_freshness(provider, cfg, args.workspace)}
    if args.json:
        print(json.dumps(report))
    else:
        if stale:
            print(f"{len(stale)} stale output(s):")
            for item in stale:
                print(f"  - {item['document']} ({item['reason']})")
        else:
            print("no stale outputs")
        derived = report["derived_export"]
        if derived.get("applicable"):
            print(f"derived export: {'fresh' if derived.get('fresh') else 'stale'}")
    return 0


def cmd_export(args) -> int:
    provider, cfg = _provider(args)
    if args.to == cfg["providers"]["authoritative"]:
        raise ConfigError(f"{args.to} is the authoritative provider; export targets the other one")
    if args.to == "markdown":
        path = Path(args.workspace) / cfg["providers"]["markdown"]["path"]
        target = {"provider": "markdown", "path": str(path)}
    else:
        bm = cfg["providers"].get("basic_memory")
        if not bm:
            raise ConfigError("no basic_memory provider is configured to export to")
        target = {
            "provider": "basic_memory",
            "vault_path": bm["vault_path"],
            "project": bm["project"],
            "folder": bm.get("folder", "career"),
        }
    summary = provider.export(target)
    print(json.dumps(summary) if args.json else f"exported derived copy to {summary['location']}")
    return 0
