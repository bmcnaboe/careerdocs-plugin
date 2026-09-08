"""careerdocs command-line interface.

Global flags (accepted after any subcommand): ``--workspace <dir>`` selects the applicant
workspace (default: the current directory) and ``--json`` requests machine-readable
output. Exit codes follow the contract: 0 ok, 1 a check failed, 2 a contract/usage error.

Feature modules register their subcommands in :func:`build_parser`; this module ships the
always-present ``version`` and ``doctor`` commands and the error-to-exit-code mapping.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import platform
import shutil
import sys
from pathlib import Path

from . import __version__, paths
from .errors import CareerDocsError

RUNTIME_DEPENDENCIES = {
    "docxtpl": "docxtpl",
    "pypdf": "pypdf",
    "pdfplumber": "pdfplumber",
    "pypdfium2": "pypdfium2",
    "jsonschema": "jsonschema",
    "python-dateutil": "dateutil",
}


def common_parent() -> argparse.ArgumentParser:
    parent = argparse.ArgumentParser(add_help=False)
    parent.add_argument(
        "--workspace",
        default=".",
        help="applicant workspace directory (default: current directory)",
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
        description="Deterministic CLI behind the career-documents flows.",
    )
    common = common_parent()
    subparsers = parser.add_subparsers(dest="command", metavar="<command>")
    subparsers.required = True

    version_parser = subparsers.add_parser(
        "version", parents=[common], help="print plugin and schema versions"
    )
    version_parser.set_defaults(func=cmd_version)

    doctor_parser = subparsers.add_parser(
        "doctor", parents=[common], help="report configuration and dependency status"
    )
    doctor_parser.set_defaults(func=cmd_doctor)

    # Feature modules contribute their subcommands here as they are implemented.
    _register_feature_commands(subparsers, common)

    return parser


def _register_feature_commands(subparsers, common: argparse.ArgumentParser) -> None:
    """Wire in each feature module's subcommands; extended as modules are added."""
    from . import brief as brief_module
    from . import config as config_module
    from . import diff as diff_module
    from . import mapping as mapping_module
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



def schema_version() -> str:
    schema = json.loads(
        (paths.SCHEMAS_DIR / "career-profile.schema.json").read_text(encoding="utf-8")
    )
    identifier = schema.get("$id", "")
    return identifier.split("#", 1)[1] if "#" in identifier else "unknown"


def dependency_status() -> dict[str, bool]:
    return {
        label: importlib.util.find_spec(module) is not None
        for label, module in RUNTIME_DEPENDENCIES.items()
    }


def cmd_version(args: argparse.Namespace) -> int:
    info = {"careerdocs": __version__, "profile_schema": schema_version()}
    if args.json:
        print(json.dumps(info))
    else:
        print(f"careerdocs {info['careerdocs']}")
        print(f"profile schema {info['profile_schema']}")
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace)
    report = {
        "workspace": str(workspace.resolve()),
        "config_present": (workspace / "career-documents.json").is_file(),
        "converter": {"soffice": shutil.which("soffice") is not None},
        "dependencies": dependency_status(),
        "python": platform.python_version(),
    }
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"workspace: {report['workspace']}")
        print(f"config present: {report['config_present']}")
        found = "found" if report["converter"]["soffice"] else "not found"
        print(f"PDF converter (soffice): {found}")
        for name, present in report["dependencies"].items():
            print(f"dependency {name}: {'ok' if present else 'missing'}")
        print(f"python: {report['python']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except CareerDocsError as exc:
        print(f"{exc.code}: {exc}", file=sys.stderr)
        return exc.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
