#!/usr/bin/env python3
"""Lint the Agent Skills under ``skills/``.

Enforces the subset of the Agent Skills specification this repository relies on, using
a small standard-library parser for the flat YAML frontmatter (one level of nesting, for
``metadata``) so the check has no third-party dependency. Rules:

* ``name`` is present, equals the skill's directory, is 1–64 characters, and is
  lowercase letters/digits/hyphens with no leading, trailing, or doubled hyphen.
* ``description`` is present and 1–1024 characters.
* ``compatibility``, when present, is at most 500 characters.
* ``metadata``, when present, is a map of string values.
* an unquoted value contains neither ``: `` nor `` #`` — strict YAML parsers, such as
  the ones cross-agent skill installers use, refuse a plain scalar with either.
* the skill body (after the frontmatter) is at most 500 lines.
* ``agents/openai.yaml``, when present, is a flat ``key: value`` file.

Prints ``path: message`` per violation and exits 1 when there is at least one.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

NAME_MAX = 64
DESCRIPTION_MAX = 1024
COMPATIBILITY_MAX = 500
BODY_MAX_LINES = 500


class FrontmatterError(ValueError):
    """The frontmatter fence or structure is malformed."""


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def _scalar(key: str, value: str) -> str:
    """Unquote ``value``; refuse a plain scalar that strict YAML parsers would reject."""
    if not (len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'"):
        for hazard in (": ", " #"):
            if hazard in value:
                raise FrontmatterError(
                    f"unquoted value of {key!r} contains {hazard!r}; quote it or rephrase"
                )
    return _unquote(value)


def parse_frontmatter(text: str) -> tuple[dict, list[str]]:
    """Parse leading ``---`` frontmatter; return ``(data, body_lines)``.

    Values are strings, except a key with only indented lines beneath it, which becomes
    a map of strings (this is how ``metadata`` is represented).
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise FrontmatterError("missing opening '---' frontmatter fence")
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        raise FrontmatterError("missing closing '---' frontmatter fence")

    fm_lines = lines[1:end]
    body_lines = lines[end + 1:]
    data: dict = {}
    i = 0
    while i < len(fm_lines):
        raw = fm_lines[i]
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            i += 1
            continue
        if raw[0] in " \t":
            raise FrontmatterError(f"unexpected indented line: {raw!r}")
        key, sep, val = raw.partition(":")
        if not sep:
            raise FrontmatterError(f"line without ':' -> {raw!r}")
        key = key.strip()
        val = val.strip()
        if val:
            data[key] = _scalar(key, val)
            i += 1
            continue
        # A key with no inline value: collect any indented lines as a nested map.
        nested: dict = {}
        j = i + 1
        while j < len(fm_lines):
            nraw = fm_lines[j]
            if not nraw.strip() or nraw.strip().startswith("#"):
                j += 1
                continue
            if nraw[0] not in " \t":
                break
            nk, nsep, nv = nraw.strip().partition(":")
            if not nsep:
                raise FrontmatterError(f"nested line without ':' -> {nraw!r}")
            nested[nk.strip()] = _scalar(f"{key}.{nk.strip()}", nv.strip())
            j += 1
        data[key] = nested if nested else ""
        i = j
    return data, body_lines


def name_errors(name: str, expected: str) -> list[str]:
    errors: list[str] = []
    if name != expected:
        errors.append(f"name {name!r} does not match directory {expected!r}")
    if not (1 <= len(name) <= NAME_MAX):
        errors.append(f"name must be 1-{NAME_MAX} characters, got {len(name)}")
    if name != name.lower():
        errors.append("name must be lowercase")
    if any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-" for c in name):
        errors.append("name may only contain lowercase letters, digits, and hyphens")
    if name.startswith("-") or name.endswith("-"):
        errors.append("name must not start or end with a hyphen")
    if "--" in name:
        errors.append("name must not contain a doubled hyphen")
    return errors


def lint_openai_yaml(path: Path) -> list[str]:
    errors: list[str] = []
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if raw[0] in " \t":
            errors.append(f"line {lineno}: indented line; openai.yaml must be flat")
            continue
        if ":" not in raw:
            errors.append(f"line {lineno}: not a 'key: value' pair")
    return errors


def lint_skill(skill_dir: Path) -> list[str]:
    """Return violation messages (each already prefixed with the file path)."""
    errors: list[str] = []
    skill_md = skill_dir / "SKILL.md"
    rel = skill_md
    if not skill_md.is_file():
        return [f"{skill_dir}/SKILL.md: missing SKILL.md"]

    try:
        data, body_lines = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
    except FrontmatterError as exc:
        return [f"{rel}: {exc}"]

    name = data.get("name")
    if not isinstance(name, str) or not name:
        errors.append(f"{rel}: missing 'name'")
    else:
        errors += [f"{rel}: {e}" for e in name_errors(name, skill_dir.name)]

    description = data.get("description")
    if not isinstance(description, str) or not description:
        errors.append(f"{rel}: missing 'description'")
    elif len(description) > DESCRIPTION_MAX:
        errors.append(f"{rel}: description exceeds {DESCRIPTION_MAX} characters")

    compatibility = data.get("compatibility")
    if isinstance(compatibility, str) and len(compatibility) > COMPATIBILITY_MAX:
        errors.append(f"{rel}: compatibility exceeds {COMPATIBILITY_MAX} characters")

    metadata = data.get("metadata")
    if metadata is not None and metadata != "":
        if not isinstance(metadata, dict):
            errors.append(f"{rel}: metadata must be a map")
        else:
            for k, v in metadata.items():
                if not isinstance(v, str):
                    errors.append(f"{rel}: metadata.{k} must be a string")

    if len(body_lines) > BODY_MAX_LINES:
        errors.append(f"{rel}: body is {len(body_lines)} lines, exceeds {BODY_MAX_LINES}")

    openai_yaml = skill_dir / "agents" / "openai.yaml"
    if openai_yaml.is_file():
        errors += [f"{openai_yaml}: {e}" for e in lint_openai_yaml(openai_yaml)]

    return errors


def lint_all(skills_dir: Path) -> list[str]:
    if not skills_dir.is_dir():
        return []
    errors: list[str] = []
    for child in sorted(skills_dir.iterdir()):
        if child.is_dir():
            errors += lint_skill(child)
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Lint Agent Skills under skills/.")
    parser.add_argument(
        "--skills-dir",
        default=str(Path(__file__).resolve().parents[1] / "skills"),
        help="directory of skills to lint (default: <repo>/skills)",
    )
    args = parser.parse_args(argv)
    errors = lint_all(Path(args.skills_dir))
    for message in errors:
        print(message)
    if errors:
        print(f"skills lint: {len(errors)} violation(s)", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
