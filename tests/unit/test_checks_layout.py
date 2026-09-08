"""Tests for the PDF checks: extraction, pagination, layout."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "skills" / "careerdocs" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from careerdocs.checks import extraction, layout, pagination  # noqa: E402

PDF = ROOT / "tests" / "fixtures" / "rendered" / "example-resume.pdf"


def test_extraction_passes_and_finds_content():
    result = extraction.check(PDF, expected_tokens=["Globex Corporation", "Python"])
    assert result["status"] == "pass"


def test_extraction_flags_missing_content():
    result = extraction.check(PDF, expected_tokens=["Nonexistent Corp"])
    assert result["status"] == "fail"


def test_extract_text_nonempty():
    assert "Kubernetes" in extraction.extract_text(PDF)


def test_pagination_within_budget():
    assert pagination.check(PDF, page_budget=2)["status"] == "pass"
    assert pagination.page_count(PDF) == 1


def test_pagination_over_budget():
    result = pagination.check(PDF, page_budget=0)
    assert result["status"] == "fail"


def test_layout_passes_margins_and_density():
    assert layout.check(PDF)["status"] == "pass"


def test_layout_renders_page_pngs(tmp_path):
    result = layout.check(PDF, out_dir=tmp_path / "layout", name="example-resume")
    assert result["status"] == "pass"
    pngs = list((tmp_path / "layout").glob("example-resume-p*.png"))
    assert len(pngs) == 1
    assert pngs[0].stat().st_size > 0


def test_layout_flags_margin_violation():
    result = layout.check(PDF, margin=300)  # absurd margin the content cannot satisfy
    assert result["status"] == "fail"
