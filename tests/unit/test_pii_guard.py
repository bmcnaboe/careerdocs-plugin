"""Tests for the applicant-data guard.

Sample PII is assembled at runtime from fragments so this test source file itself
carries no matchable token — otherwise the guard, scanning the whole tree in the final
gate, would flag its own test.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import pii_guard  # noqa: E402

AT = "@"


def test_flags_real_email():
    text = "Reach me at jane.doe" + AT + "acme-corp.com any time."
    findings = pii_guard.scan_text(text)
    assert any("email" in desc for _, desc in findings)


def test_allows_example_domains():
    text = (
        "Contact applicant" + AT + "example.com or hr" + AT + "example.org"
    )
    assert pii_guard.scan_text(text) == []


def test_allows_subdomain_of_example():
    text = "someone" + AT + "mail.example.com"
    assert pii_guard.scan_text(text) == []


def test_flags_non_555_phone():
    number = "617" + "-234-5678"
    findings = pii_guard.scan_text(f"Call {number} for details")
    assert any("telephone" in desc for _, desc in findings)


def test_allows_555_phone():
    number = "(212) " + "555-0143"
    assert pii_guard.scan_text(f"Call {number}") == []


def test_ignores_bare_digit_runs():
    # An id / timestamp, not a phone number: no separators, so it must not match.
    assert pii_guard.scan_text("build 1234567890 completed") == []


def test_ignores_iso_dates():
    assert pii_guard.scan_text("Created 2026-09-07 by the loop") == []


def test_flags_street_address():
    addr = "42 " + "Elm Street"
    findings = pii_guard.scan_text(f"Lives at {addr}, apt 3")
    assert any("street address" in desc for _, desc in findings)


def test_reports_line_numbers():
    number = "617" + "-234-5678"
    text = "clean line\nanother clean line\ncall " + number
    findings = pii_guard.scan_text(text)
    assert findings and findings[0][0] == 3


def test_exclusion_prefixes():
    assert pii_guard.is_excluded("examples/applicant/careerdocs.json")
    assert pii_guard.is_excluded("tests/fixtures/candidates.json")
    assert not pii_guard.is_excluded("skills/careerdocs/SKILL.md")


def test_scan_file_skips_binary(tmp_path):
    binary = tmp_path / "blob.bin"
    payload = ("contact" + AT + "hidden.io").encode("utf-8")
    binary.write_bytes(b"\xff\xfe\x00\x01" + payload + b"\xff")
    assert pii_guard.scan_file(binary) == []


def test_scan_file_reads_text(tmp_path):
    bad = tmp_path / "leak.txt"
    bad.write_text("mail me at contact" + AT + "realestate.io", encoding="utf-8")
    findings = pii_guard.scan_file(bad)
    assert any("email" in desc for _, desc in findings)


def test_repo_tree_is_clean():
    # The guard must find nothing in the actual tracked tree.
    assert pii_guard.scan_repo(ROOT) == []
