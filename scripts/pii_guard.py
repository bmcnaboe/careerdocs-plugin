#!/usr/bin/env python3
"""Applicant-data guard.

Hard rule of this repository: no applicant data, ever. This scans every tracked file
outside the sanitized fixture trees (``examples/`` and ``tests/fixtures/``) for tokens
that look like real personal data — email addresses on a domain other than the reserved
``example.com`` / ``example.org``, telephone numbers that do not use the fictional
``555`` exchange, and US-style street addresses. It prints ``path:line: <what>`` for
every finding and exits 1 when there is at least one, so the final gate fails before
personal data can land.

Standard library only. Importable: ``scan_text`` is the detector, ``main`` wires it to
``git ls-files``.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ALLOWED_EMAIL_DOMAINS = ("example.com", "example.org")
EXCLUDED_PREFIXES = ("examples/", "tests/fixtures/")

# An email address; the domain is checked against the allowlist after matching.
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

# A US/NANP telephone number written with separators, parens, or a country code.
# Bare digit runs are intentionally not matched — those are IDs, not phone numbers.
PHONE_RE = re.compile(
    r"(?<![\dA-Za-z])"
    r"(?:\+?1[\s.\-])?"
    r"(?:\(\d{3}\)\s?|\d{3}[\s.\-])"
    r"\d{3}[\s.\-]\d{4}"
    r"(?![\dA-Za-z])"
)

# A street address: a house number, one to four capitalized words, and a street suffix.
_STREET_SUFFIX = (
    r"Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|"
    r"Way|Place|Pl|Terrace|Ter|Circle|Cir|Highway|Hwy|Parkway|Pkwy"
)
STREET_RE = re.compile(
    r"\b\d{1,6}\s+(?:[A-Z][A-Za-z]*\.?\s+){1,4}(?:" + _STREET_SUFFIX + r")\b\.?"
)


def scan_text(text: str) -> list[tuple[int, str]]:
    """Return ``(line_number, description)`` for every PII token in ``text``."""
    findings: list[tuple[int, str]] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        for match in EMAIL_RE.finditer(line):
            domain = match.group(0).rsplit("@", 1)[1].lower()
            if not any(domain == d or domain.endswith("." + d) for d in ALLOWED_EMAIL_DOMAINS):
                findings.append((lineno, f"email address {match.group(0)!r}"))
        for match in PHONE_RE.finditer(line):
            digits = re.sub(r"\D", "", match.group(0))
            if "555" not in digits:
                findings.append((lineno, f"telephone number {match.group(0).strip()!r}"))
        for match in STREET_RE.finditer(line):
            findings.append((lineno, f"street address {match.group(0)!r}"))
    return findings


def is_excluded(relpath: str) -> bool:
    return any(relpath.startswith(prefix) for prefix in EXCLUDED_PREFIXES)


def tracked_files(root: Path) -> list[str]:
    out = subprocess.run(
        ["git", "ls-files"],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )
    return [line for line in out.stdout.splitlines() if line]


def scan_file(path: Path) -> list[tuple[int, str]]:
    """Scan one file; binary files (undecodable as UTF-8) are skipped."""
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return []
    return scan_text(text)


def scan_repo(root: Path) -> list[tuple[str, int, str]]:
    results: list[tuple[str, int, str]] = []
    for relpath in tracked_files(root):
        if is_excluded(relpath):
            continue
        for lineno, desc in scan_file(root / relpath):
            results.append((relpath, lineno, desc))
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fail the build on applicant data.")
    parser.add_argument(
        "--root",
        default=str(Path(__file__).resolve().parents[1]),
        help="repository root to scan (default: the repository this script lives in)",
    )
    args = parser.parse_args(argv)
    root = Path(args.root)
    findings = scan_repo(root)
    for relpath, lineno, desc in findings:
        print(f"{relpath}:{lineno}: {desc}")
    if findings:
        print(f"applicant-data guard: {len(findings)} finding(s)", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
