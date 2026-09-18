"""Render history: git commits when the workspace is versioned, ``archive/`` otherwise.

A workspace inside a git work tree keeps its history in git: ``render`` overwrites the
current documents in place (committing an uncommitted previous render first, so nothing
is lost), and ``commit`` records each generation or revision round — the application
folder, the workflow state for that subject, and the profile when the round changed
it — under a Conventional Commit message. Nothing else in the work tree is staged, so
unrelated edits stay untouched. Without git the previous render moves to
``outputs/archive/`` under its generation stamp, as before.

``outputs.history`` in the config chooses: ``auto`` (the default: git when the workspace
sits in a work tree with a committer identity), ``git`` (required), or ``archive``
(never git).
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path

from . import config as config_module
from .errors import CareerDocsError

MODES = ("auto", "git", "archive")


def _git(directory, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(directory), *args], capture_output=True, text=True)


def repository(workspace) -> Path | None:
    """The work tree holding ``workspace``, when git is on PATH, the workspace is inside
    a repository, and git can name a committer; otherwise None."""
    if shutil.which("git") is None:
        return None
    result = _git(workspace, "rev-parse", "--show-toplevel")
    if result.returncode != 0:
        return None
    if _git(workspace, "var", "GIT_COMMITTER_IDENT").returncode != 0:
        return None
    return Path(result.stdout.strip())


def mode(workspace, cfg: dict) -> str:
    """``git`` or ``archive`` for this workspace, honoring ``outputs.history``."""
    setting = cfg["outputs"].get("history", "auto")
    if setting == "archive":
        return "archive"
    repo = repository(workspace)
    if repo is None:
        if setting == "git":
            raise CareerDocsError(
                "outputs.history is 'git' but the workspace is not inside a git repository "
                "with a committer identity (git config user.name / user.email)", code="USAGE")
        return "archive"
    return "git"


def changed(workspace, paths) -> list[Path]:
    """The files under ``paths`` that git sees as modified, deleted, or untracked."""
    repo = repository(workspace)
    if repo is None:
        return []
    pathspecs = [str(Path(p)) for p in paths]
    if not pathspecs:
        return []
    result = _git(repo, "status", "--porcelain=v1", "-z", "--untracked-files=all", "--", *pathspecs)
    if result.returncode != 0:
        raise CareerDocsError(f"git status failed: {result.stderr.strip()}")
    files: list[Path] = []
    tokens = result.stdout.split("\0")
    index = 0
    while index < len(tokens):
        entry = tokens[index]
        index += 1
        if len(entry) < 4:
            continue
        status, path = entry[:2], entry[3:]
        files.append(repo / path)
        if status[0] in "RC":  # a rename or copy carries the original path in the next token
            index += 1
    return files


def commit(workspace, paths, message: str) -> str | None:
    """Stage the changed files under ``paths`` and commit them; return the short hash,
    or None when nothing under ``paths`` had changed."""
    files = changed(workspace, paths)
    if not files:
        return None
    repo = repository(workspace)
    specs = [str(f) for f in files]
    added = _git(repo, "add", "-A", "--", *specs)
    if added.returncode != 0:
        raise CareerDocsError(f"git add failed: {added.stderr.strip()}")
    committed = _git(repo, "commit", "--quiet", "-m", message, "--", *specs)
    if committed.returncode != 0:
        raise CareerDocsError(f"git commit failed: {(committed.stderr or committed.stdout).strip()}")
    return _git(repo, "rev-parse", "--short", "HEAD").stdout.strip()


def round_paths(workspace, cfg: dict, *, slug: str | None = None, baseline: str | None = None,
                extra=()) -> list[Path]:
    """What one round may have touched: the application folder and the workflow state for
    that subject, or the baseline folder, plus the profile provider's directory and any
    extra paths (a setup round names the config, templates, voice, and identity)."""
    root = Path(workspace)
    paths: list[Path] = []
    if baseline:
        paths.append(root / cfg["outputs"]["baselines_dir"] / baseline)
    if slug:
        paths.append(root / cfg["outputs"]["applications_dir"] / slug)
        state_dir = root / cfg["workflow"]["state_dir"]
        if state_dir.is_dir():
            paths += sorted(state_dir.glob(f"*/{slug}.json"))
    paths.append(root / cfg["providers"]["markdown"]["path"])
    paths += [Path(p) if Path(p).is_absolute() else root / p for p in extra]
    return paths


# --- CLI ---


def register(subparsers, common: argparse.ArgumentParser) -> None:
    parser = subparsers.add_parser("commit", parents=[common],
                                   help="commit a generation or revision round when the workspace is in git")
    parser.add_argument("--role-slug", help="the application this round produced")
    parser.add_argument("--baseline", action="store_true", help="commit a baseline round instead")
    parser.add_argument("--positioning", choices=["executive", "builder"], help="baseline positioning")
    parser.add_argument("--message", "-m", required=True, help="Conventional Commit message, e.g. 'feat(<slug>): first résumé and letter'")
    parser.add_argument("--path", action="append", default=[], metavar="PATH",
                        help="a workspace path this round changed, relative to the workspace (repeatable)")
    parser.set_defaults(func=cmd_commit)


def cmd_commit(args) -> int:
    cfg = config_module.resolve_config(args.workspace)
    if not (args.baseline or args.role_slug or args.path):
        raise CareerDocsError("specify --role-slug, --baseline, or --path", code="USAGE")
    positioning = (args.positioning or cfg["workflow"]["positioning_default"]) if args.baseline else None
    paths = round_paths(args.workspace, cfg, slug=args.role_slug, baseline=positioning, extra=args.path)

    history = mode(args.workspace, cfg)
    if history != "git":
        result = {"history": history, "committed": None}
        print(json.dumps(result) if args.json else "no git repository: the archive holds the history; nothing to commit")
        return 0
    sha = commit(args.workspace, paths, args.message)
    if args.json:
        print(json.dumps({"history": "git", "committed": sha, "paths": [str(p) for p in paths]}))
    elif sha:
        print(f"committed {sha}: {args.message}")
    else:
        print("nothing to commit: no changes under this round's paths")
    return 0
