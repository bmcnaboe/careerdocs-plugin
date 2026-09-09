"""Move a workspace into the documented structure from a reviewed inventory.

``organize --inventory <file>`` reads an ``inventory.json`` and moves each file under its
proposed destination (``sources/``, ``templates/``, ``voice/``, ``baselines/``,
``applications/``, ``archive/``, ``.careerdocs/``), preserving each file's original
sub-path under the destination so the move is unique and recoverable. It **never deletes**:
duplicates, temporary files, and unrelated items are relocated under ``archive/``. Every
move is appended to ``.careerdocs/moves.jsonl``; ``--rollback`` replays it in reverse.
``--dry-run`` previews without changing anything.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import util
from .errors import CareerDocsError

MOVES_LOG = Path(".careerdocs") / "moves.jsonl"


def plan_moves(inventory: dict) -> list[tuple[str, str]]:
    """Return ``(src_rel, dst_rel)`` for every file that should move."""
    moves: list[tuple[str, str]] = []
    for entry in inventory["files"]:
        src_rel = entry["path"]
        dest = entry["destination"].rstrip("/")
        dst_rel = f"{dest}/{src_rel}" if dest else src_rel
        if dst_rel != src_rel:
            moves.append((src_rel, dst_rel))
    return moves


def read_moves(root: Path) -> list[dict]:
    log = root / MOVES_LOG
    if not log.is_file():
        return []
    return [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines() if line.strip()]


def _append_move(root: Path, record: dict) -> None:
    log = root / MOVES_LOG
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record) + "\n")


def apply_moves(root: Path, moves: list[tuple[str, str]], *, dry_run: bool = False) -> list[dict]:
    import shutil

    performed: list[dict] = []
    for src_rel, dst_rel in moves:
        src = root / src_rel
        dst = root / dst_rel
        if not src.exists():
            continue
        record = {"from": src_rel, "to": dst_rel, "at": util.now()}
        performed.append(record)
        if dry_run:
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        _append_move(root, record)
    return performed


def _prune_empty_parents(root: Path, directory: Path) -> None:
    directory = directory.resolve()
    root = root.resolve()
    while directory != root and directory.is_dir() and not any(directory.iterdir()):
        directory.rmdir()
        directory = directory.parent


def rollback(root: Path, *, dry_run: bool = False) -> list[dict]:
    import shutil

    entries = read_moves(root)
    undone: list[dict] = []
    for record in reversed(entries):
        src = root / record["to"]
        dst = root / record["from"]
        if not src.exists():
            continue
        undone.append({"from": record["to"], "to": record["from"]})
        if dry_run:
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        _prune_empty_parents(root, src.parent)
    if not dry_run and entries:
        (root / MOVES_LOG).unlink()
    return undone


# --- CLI ---


def register(subparsers, common: argparse.ArgumentParser) -> None:
    parser = subparsers.add_parser("organize", parents=[common], help="move a workspace into the documented structure")
    parser.add_argument("--inventory", required=True, help="inventory.json to act on")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true", help="perform the moves")
    mode.add_argument("--rollback", action="store_true", help="undo the recorded moves")
    parser.add_argument("--dry-run", action="store_true", help="preview without changing anything")
    parser.set_defaults(func=cmd_organize, needs_workspace=False)


def cmd_organize(args) -> int:
    inventory_path = Path(args.inventory)
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    root = Path(inventory["root"])

    if args.rollback:
        undone = rollback(root, dry_run=args.dry_run)
        verb = "would undo" if args.dry_run else "undid"
        if args.json:
            print(json.dumps({"rolled_back": len(undone), "dry_run": args.dry_run}))
        else:
            print(f"{verb} {len(undone)} move(s)")
        return 0

    dry_run = args.dry_run or not args.apply
    moves = apply_moves(root, plan_moves(inventory), dry_run=dry_run)
    if args.json:
        print(json.dumps({"moves": len(moves), "dry_run": dry_run}))
    else:
        verb = "would move" if dry_run else "moved"
        print(f"{verb} {len(moves)} file(s)")
        if dry_run:
            for record in moves:
                print(f"  {record['from']} -> {record['to']}")
    return 0
