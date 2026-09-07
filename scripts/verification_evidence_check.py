#!/usr/bin/env python3
"""Verification-evidence traceability check.

Every acceptance scenario in the design spec must have a row in the design's
verification-evidence table, and every such row must name concrete evidence. This
parses the numbered acceptance scenarios out of ``design/spec.md`` (scenario ``US<n>-<m>``
= the m-th scenario under "User Story n") and the rows of ``design/verification-evidence.md``,
then fails when a scenario has no row or a row has no evidence. ``--require-complete``
additionally fails on any row still marked ``pending``.

Standard library only.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

STORY_RE = re.compile(r"^###\s+User Story\s+(\d+)\b")
SCENARIO_ITEM_RE = re.compile(r"^(\d+)\.\s")
SCENARIO_ID_RE = re.compile(r"^US\d+-\d+$")


def parse_spec_scenarios(text: str) -> set[str]:
    """Return the set of ``US<n>-<m>`` scenario ids declared in the spec."""
    scenarios: set[str] = set()
    current_story: int | None = None
    in_scenarios = False
    for line in text.splitlines():
        story = STORY_RE.match(line)
        if story:
            current_story = int(story.group(1))
            in_scenarios = False
            continue
        if line.startswith("## ") and not line.startswith("### "):
            current_story = None
            in_scenarios = False
            continue
        if line.startswith("### "):
            in_scenarios = False
            continue
        if current_story is not None and "**Acceptance Scenarios**" in line:
            in_scenarios = True
            continue
        if in_scenarios and current_story is not None:
            item = SCENARIO_ITEM_RE.match(line)
            if item:
                scenarios.add(f"US{current_story}-{int(item.group(1))}")
    return scenarios


def parse_evidence_rows(text: str) -> dict[str, tuple[str, str]]:
    """Return ``scenario_id -> (evidence, status)`` from the evidence table."""
    rows: dict[str, tuple[str, str]] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if len(cells) < 4:
            continue
        scenario = cells[0]
        if not SCENARIO_ID_RE.match(scenario):
            continue
        rows[scenario] = (cells[2], cells[3].lower())
    return rows


def check(
    spec_scenarios: set[str],
    evidence_rows: dict[str, tuple[str, str]],
    require_complete: bool = False,
) -> list[str]:
    errors: list[str] = []
    for scenario in sorted(spec_scenarios):
        if scenario not in evidence_rows:
            errors.append(f"{scenario}: no row in verification-evidence.md")
    for scenario, (evidence, status) in sorted(evidence_rows.items()):
        if not evidence:
            errors.append(f"{scenario}: row has no evidence")
        if require_complete and status == "pending":
            errors.append(f"{scenario}: status is still pending")
    return errors


def resolve_paths(root: Path, run_dir: str | None) -> tuple[Path, Path]:
    if run_dir:
        design = Path(run_dir) / "design"
        return design / "spec.md", design / "verification-evidence.md"
    candidates = [
        d
        for d in sorted((root / "linear-specs").glob("*/design"))
        if (d / "spec.md").is_file() and (d / "verification-evidence.md").is_file()
    ]
    if len(candidates) == 1:
        d = candidates[0]
        return d / "spec.md", d / "verification-evidence.md"
    if not candidates:
        raise SystemExit("no linear-specs/*/design with spec.md and verification-evidence.md")
    raise SystemExit("multiple run directories found; pass --run-dir")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check verification-evidence traceability.")
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--run-dir", default=None, help="linear-specs/<stamp>-<slug> directory")
    parser.add_argument(
        "--require-complete",
        action="store_true",
        help="also fail on any row still marked pending",
    )
    args = parser.parse_args(argv)

    spec_path, evidence_path = resolve_paths(Path(args.root), args.run_dir)
    spec_scenarios = parse_spec_scenarios(spec_path.read_text(encoding="utf-8"))
    evidence_rows = parse_evidence_rows(evidence_path.read_text(encoding="utf-8"))
    errors = check(spec_scenarios, evidence_rows, require_complete=args.require_complete)

    for message in errors:
        print(message)
    if errors:
        print(f"verification evidence: {len(errors)} problem(s)", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
