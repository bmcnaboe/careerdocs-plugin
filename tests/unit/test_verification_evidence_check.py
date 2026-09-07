"""Tests for the verification-evidence traceability check."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import verification_evidence_check as vec  # noqa: E402

SPEC = """\
## User Scenarios & Testing

### User Story 1 - Install (Priority: P1)

**Acceptance Scenarios**:

1. **Given** a, **When** b, **Then** c.
2. **Given** d, **When** e, **Then** f.

### Edge Cases

- something

### User Story 2 - Onboard (Priority: P1)

**Acceptance Scenarios**:

1. **Given** g, **When** h, **Then** i.

## Requirements

1. FR-001 not a scenario.
"""


def _evidence(rows: str) -> str:
    header = (
        "| Scenario | Method | Evidence | Status |\n"
        "| -------- | ------ | -------- | ------ |\n"
    )
    return header + rows


def test_parses_scenarios_per_story():
    assert vec.parse_spec_scenarios(SPEC) == {"US1-1", "US1-2", "US2-1"}


def test_requirements_numbers_not_treated_as_scenarios():
    # The numbered FR under Requirements must not become a scenario.
    scenarios = vec.parse_spec_scenarios(SPEC)
    assert not any(s.startswith("US3") for s in scenarios)


def test_parses_evidence_rows():
    table = _evidence(
        "| US1-1 | contract | some.py | pass |\n"
        "| US1-2 | unit | other.py | pending |\n"
    )
    rows = vec.parse_evidence_rows(table)
    assert rows["US1-1"] == ("some.py", "pass")
    assert rows["US1-2"] == ("other.py", "pending")


def test_missing_row_fails():
    rows = vec.parse_evidence_rows(_evidence("| US1-1 | c | e.py | pass |\n"))
    errors = vec.check({"US1-1", "US1-2"}, rows)
    assert any("US1-2: no row" in e for e in errors)


def test_empty_evidence_fails():
    rows = vec.parse_evidence_rows(_evidence("| US1-1 | contract |  | pass |\n"))
    errors = vec.check({"US1-1"}, rows)
    assert any("US1-1: row has no evidence" in e for e in errors)


def test_all_present_passes():
    rows = vec.parse_evidence_rows(_evidence("| US1-1 | contract | e.py | pass |\n"))
    assert vec.check({"US1-1"}, rows) == []


def test_require_complete_flags_pending():
    rows = vec.parse_evidence_rows(_evidence("| US1-1 | contract | e.py | pending |\n"))
    assert vec.check({"US1-1"}, rows) == []
    errors = vec.check({"US1-1"}, rows, require_complete=True)
    assert any("still pending" in e for e in errors)


def test_repo_spec_and_evidence_consistent():
    spec_path, evidence_path = vec.resolve_paths(ROOT, None)
    scenarios = vec.parse_spec_scenarios(spec_path.read_text(encoding="utf-8"))
    rows = vec.parse_evidence_rows(evidence_path.read_text(encoding="utf-8"))
    # Every spec scenario has a row with evidence (statuses may still be pending).
    assert vec.check(scenarios, rows) == []
