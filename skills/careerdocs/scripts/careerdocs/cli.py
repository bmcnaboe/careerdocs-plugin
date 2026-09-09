"""careerdocs command-line interface.

Global flags (accepted after any subcommand): ``--workspace <dir>`` overrides the
applicant workspace (otherwise resolved as :mod:`workspace` describes) and ``--json``
requests machine-readable output. Exit codes follow the contract: 0 ok, 1 a check failed,
2 a contract/usage error.

A subcommand that sets a workspace up, or never touches one, registers with
``set_defaults(needs_workspace=False)``; every other command refuses to run against a
directory nothing marks as a workspace.

Feature modules register their subcommands in :func:`build_parser`; this module ships the
always-present ``version`` and ``doctor`` commands and the error-to-exit-code mapping.
"""

from __future__ import annotations

import argparse
import json
import platform
import shutil
import sys
from pathlib import Path

from . import __version__, deps, paths, workspace
from .errors import CareerDocsError


def common_parent() -> argparse.ArgumentParser:
    parent = argparse.ArgumentParser(add_help=False)
    parent.add_argument(
        "--workspace",
        default=None,
        help="applicant workspace directory (default: CAREERDOCS_WORKSPACE, the nearest "
        "careerdocs.json, the recorded default, then the current directory)",
    )
    parent.add_argument(
        "--json",
        action="store_true",
        help="emit machine-readable JSON on stdout",
    )
    return parent


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="careerdocs",
        description="Deterministic CLI behind the careerdocs flows.",
    )
    common = common_parent()
    subparsers = parser.add_subparsers(dest="command", metavar="<command>")
    subparsers.required = True

    version_parser = subparsers.add_parser(
        "version", parents=[common], help="print plugin and schema versions"
    )
    version_parser.set_defaults(func=cmd_version, needs_workspace=False)

    doctor_parser = subparsers.add_parser(
        "doctor", parents=[common], help="report configuration and dependency status"
    )
    doctor_parser.set_defaults(func=cmd_doctor, needs_workspace=False)

    # Feature modules contribute their subcommands here as they are implemented.
    _register_feature_commands(subparsers, common)

    return parser


def _register_feature_commands(subparsers, common: argparse.ArgumentParser) -> None:
    """Wire in each feature module's subcommands; extended as modules are added."""
    from . import brief as brief_module
    from . import config as config_module
    from . import diff as diff_module
    from . import inventory as inventory_module
    from . import mapping as mapping_module
    from . import organize as organize_module
    from . import plan as plan_module
    from . import record as record_module
    from . import render as render_module
    from . import state as state_module

    config_module.register(subparsers, common)
    diff_module.register(subparsers, common)
    state_module.register(subparsers, common)
    brief_module.register(subparsers, common)
    mapping_module.register(subparsers, common)
    plan_module.register(subparsers, common)
    render_module.register(subparsers, common)
    record_module.register(subparsers, common)
    inventory_module.register(subparsers, common)
    organize_module.register(subparsers, common)



def schema_version() -> str:
    schema = json.loads(
        (paths.SCHEMAS_DIR / "career-profile.schema.json").read_text(encoding="utf-8")
    )
    identifier = schema.get("$id", "")
    return identifier.split("#", 1)[1] if "#" in identifier else "unknown"


def dependency_status() -> dict[str, bool]:
    return deps.status()


def cmd_version(args: argparse.Namespace) -> int:
    info = {"careerdocs": __version__, "profile_schema": schema_version()}
    if args.json:
        print(json.dumps(info))
    else:
        print(f"careerdocs {info['careerdocs']}")
        print(f"profile schema {info['profile_schema']}")
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    from . import config as config_module
    from .providers import load_provider
    from .workspace import SOURCE_LABELS

    workspace = Path(args.workspace)
    config_present = (workspace / "careerdocs.json").is_file()
    try:
        cfg = config_module.resolve_config(workspace)
        config_valid, config_error = True, None
    except CareerDocsError as exc:
        cfg = config_module.default_config()
        config_valid, config_error = False, str(exc)

    try:
        provider = load_provider(workspace, cfg)
        profile = provider.read()
        provider_status = {
            "authoritative": cfg["providers"]["authoritative"],
            "reachable": True,
            "entities": len(profile["entities"]),
        }
    except CareerDocsError as exc:
        provider_status = {
            "authoritative": cfg["providers"]["authoritative"],
            "reachable": False,
            "error": str(exc),
        }

    templates_dir = workspace / cfg["templates"]["dir"]
    templates = {
        "resume": (templates_dir / cfg["templates"]["resume"] / "template.docx").is_file(),
        "cover_letter": (templates_dir / cfg["templates"]["cover_letter"] / "template.docx").is_file(),
    }
    voice = {
        "path": cfg["voice"]["path"],
        "present": (workspace / cfg["voice"]["path"]).is_file(),
    }

    report = {
        "workspace": str(workspace.resolve()),
        "workspace_source": args.workspace_source,
        "config_present": config_present,
        "config_valid": config_valid,
        "config_error": config_error,
        "provider": provider_status,
        "templates": templates,
        "voice": voice,
        "converter": {"soffice": shutil.which("soffice") is not None},
        "dependencies": dependency_status(),
        "python": platform.python_version(),
    }
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        source = SOURCE_LABELS[report["workspace_source"]]
        print(f"workspace: {report['workspace']} (via {source})")
        print(f"config: {'present' if config_present else 'absent (defaults)'}"
              f"{'' if config_valid else ' — INVALID: ' + str(config_error)}")
        prov = report["provider"]
        print(f"provider ({prov['authoritative']}): "
              + (f"reachable, {prov['entities']} entities" if prov["reachable"] else f"UNREACHABLE: {prov['error']}"))
        print(f"template (resume): {'present' if templates['resume'] else 'missing'}")
        print(f"template (cover letter): {'present' if templates['cover_letter'] else 'missing'}")
        print(f"voice ({voice['path']}): {'present' if voice['present'] else 'missing'}")
        print(f"PDF converter (soffice): {'found' if report['converter']['soffice'] else 'not found'}")
        for name, present in report["dependencies"].items():
            print(f"dependency {name}: {'ok' if present else 'missing'}")
        print(f"python: {report['python']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        located = workspace.resolve(getattr(args, "workspace", None))
        if getattr(args, "needs_workspace", True):
            workspace.ensure_established(located)
        args.workspace = str(located.path)
        args.workspace_source = located.source
        return args.func(args)
    except CareerDocsError as exc:
        print(f"{exc.code}: {exc}", file=sys.stderr)
        return exc.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
