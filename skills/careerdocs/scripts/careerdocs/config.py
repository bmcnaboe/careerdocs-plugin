"""Workspace configuration (``careerdocs.json``).

The config only *locates* the four authorities; it never stores qualifications or
credentials. This module provides the defaults for every key, a deep-merged resolved
view for the rest of the CLI, validation against ``config.schema.json``, refusal of
credential-like or qualification-like content, and the ``config init`` / ``config
validate`` subcommands.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import jsonschema

from . import paths
from .errors import ConfigError

CONFIG_FILENAME = "careerdocs.json"

# Every key with its default. basic_memory is intentionally omitted: it has required
# sub-keys, so it is only present when the applicant opts into that provider.
DEFAULT_CONFIG: dict = {
    "version": "1",
    "providers": {
        "authoritative": "markdown",
        "markdown": {"path": "profile"},
    },
    "templates": {"dir": "templates", "resume": "resume", "cover_letter": "cover-letter"},
    "voice": {"path": "voice/voice.md"},
    "outputs": {"applications_dir": "applications", "baselines_dir": "baselines"},
    "workflow": {
        "state_dir": ".careerdocs/state",
        "positioning_default": "builder",
        "page_budget": {"resume": 2, "cover_letter": 1},
        "approval_mode": "explicit",
    },
}

FORBIDDEN_KEYS = {
    "password",
    "token",
    "api_key",
    "secret",
    "entities",
    "experience",
    "skills",
    "achievements",
}
CREDENTIAL_MARKERS = ("password", "token", "api_key", "secret")


def default_config() -> dict:
    """A fresh, fully-defaulted config suitable for writing."""
    return json.loads(json.dumps(DEFAULT_CONFIG))


def config_path(workspace: str | Path) -> Path:
    return Path(workspace) / CONFIG_FILENAME


def _deep_merge(base: dict, override: dict) -> dict:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_raw(workspace: str | Path) -> dict | None:
    """Return the parsed config file, or None when it is absent."""
    path = config_path(workspace)
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigError(f"{CONFIG_FILENAME} is not valid JSON: {exc}") from exc


def resolve_config(workspace: str | Path) -> dict:
    """The effective config: defaults deep-merged with the file's values (if any)."""
    raw = load_raw(workspace)
    if raw is None:
        return default_config()
    check_forbidden(raw)
    validate_schema(raw)
    return _deep_merge(DEFAULT_CONFIG, raw)


def find_forbidden(obj, path: str = "") -> list[str]:
    problems: list[str] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            where = f"{path}.{key}" if path else key
            if key.lower() in FORBIDDEN_KEYS:
                problems.append(f"forbidden key {key!r} at {where}")
            problems += find_forbidden(value, where)
    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            problems += find_forbidden(value, f"{path}[{i}]")
    elif isinstance(obj, str):
        low = obj.lower()
        if any(marker in low for marker in CREDENTIAL_MARKERS):
            problems.append(f"credential-like value at {path or '<root>'}")
    return problems


def check_forbidden(data: dict) -> None:
    problems = find_forbidden(data)
    if problems:
        raise ConfigError("config stores forbidden content: " + "; ".join(problems))


def _config_schema() -> dict:
    return json.loads(
        (paths.SCHEMAS_DIR / "config.schema.json").read_text(encoding="utf-8")
    )


def validate_schema(data: dict) -> None:
    # The shipped schemas encode their version in the ``$id`` fragment, which the strict
    # 2020-12 metaschema disallows; instantiate the validator directly so it validates the
    # instance without first self-checking the schema.
    validator = jsonschema.Draft202012Validator(_config_schema())
    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.path))
    if errors:
        raise ConfigError(f"config is invalid: {errors[0].message}")


def register(subparsers, common: argparse.ArgumentParser) -> None:
    config_parser = subparsers.add_parser(
        "config", help="manage the workspace careerdocs.json"
    )
    actions = config_parser.add_subparsers(dest="config_command", metavar="<action>")
    actions.required = True

    init_parser = actions.add_parser(
        "init", parents=[common], help="write a default config if none exists"
    )
    init_parser.set_defaults(func=cmd_init)

    validate_parser = actions.add_parser(
        "validate", parents=[common], help="validate the config and refuse forbidden keys"
    )
    validate_parser.set_defaults(func=cmd_validate)


def cmd_init(args: argparse.Namespace) -> int:
    path = config_path(args.workspace)
    if path.exists():
        message = f"{CONFIG_FILENAME} already exists; leaving it untouched"
        print(json.dumps({"created": False, "path": str(path)}) if args.json else message)
        return 0
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(default_config(), indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"created": True, "path": str(path)}) if args.json else f"wrote {path}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    raw = load_raw(args.workspace)
    if raw is None:
        message = f"no {CONFIG_FILENAME}; defaults apply"
        print(json.dumps({"valid": True, "present": False}) if args.json else message)
        return 0
    check_forbidden(raw)
    validate_schema(raw)
    print(json.dumps({"valid": True, "present": True}) if args.json else "config is valid")
    return 0
