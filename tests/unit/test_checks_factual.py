"""Tests for the factual and links/dates checks."""

import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "skills" / "career-documents" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from careerdocs import brief, diff, mapping, merge, plan, render  # noqa: E402
from careerdocs.checks import factual, links_dates  # noqa: E402
from careerdocs.config import default_config  # noqa: E402
from careerdocs.providers import load_provider  # noqa: E402

CANDIDATES = json.loads((ROOT / "tests" / "fixtures" / "candidates.json").read_text())
JD = (ROOT / "examples" / "applicant" / "applications" / "example-role" / "job-description.md").read_text()
TEMPLATE_DIR = ROOT / "examples" / "applicant" / "templates" / "resume"
TEMPLATE_JSON = json.loads((TEMPLATE_DIR / "template.json").read_text())


def build(tmp_path):
    provider = load_provider(tmp_path, default_config())
    ops = merge.build_operations(provider.read(), CANDIDATES)
    d = diff.make_diff(provider, ops)
    diff.approve(provider, d["diff_id"])
    diff.apply(provider, d["diff_id"], cfg=default_config(), workspace=tmp_path)
    b = brief.generate_brief(JD)
    m = mapping.generate_map(b, provider.read())
    p = plan.generate_plan(m, provider.read(), TEMPLATE_JSON, "builder")
    out = tmp_path / "resume.docx"
    render.render_document(p, TEMPLATE_JSON, TEMPLATE_DIR / "template.docx", out)
    text = "\n".join(par.text for par in __import__("docx").Document(str(out)).paragraphs)
    return p, provider.read(), text


# --- factual ---


def test_factual_passes_on_real_render(tmp_path):
    p, profile, text = build(tmp_path)
    result = factual.check(text, p, profile, allowlist=TEMPLATE_JSON["allowlist"])
    assert result["status"] == "pass", result["details"]


def test_factual_flags_invented_number(tmp_path):
    p, profile, text = build(tmp_path)
    tampered = text + "\nGrew revenue by 999 percent."
    result = factual.check(tampered, p, profile, allowlist=TEMPLATE_JSON["allowlist"])
    assert result["status"] == "fail"
    assert "999" in result["details"]


def test_factual_flags_unsourced_line(tmp_path):
    p, profile, text = build(tmp_path)
    tampered = text + "\nLed the FDA medical device program."
    result = factual.check(tampered, p, profile, allowlist=TEMPLATE_JSON["allowlist"])
    assert result["status"] == "fail"
    assert "unsourced line" in result["details"]


def test_factual_allowlist_permits_section_titles(tmp_path):
    p, profile, text = build(tmp_path)
    # "Experience" is a section title; only passes because it is allowlisted.
    without_allowlist = factual.check(text, p, profile, allowlist=[])
    assert without_allowlist["status"] == "fail"


# --- links_dates ---


def test_links_dates_passes_on_real_render(tmp_path):
    _, _, text = build(tmp_path)
    assert links_dates.check(text)["status"] == "pass"


def test_links_dates_flags_future_date():
    result = links_dates.check("Worked 2099-01 to present", today=date(2026, 1, 1))
    assert result["status"] == "fail" and "future" in result["details"]


def test_links_dates_flags_out_of_order_range():
    result = links_dates.check("Studied 2015–2011", today=date(2026, 1, 1))
    assert result["status"] == "fail" and "out of order" in result["details"]


def test_links_dates_flags_malformed_link():
    result = links_dates.check("See https://broken")
    assert result["status"] == "fail" and "malformed link" in result["details"]


def test_links_dates_valid_link_offline_skips_liveness():
    result = links_dates.check("See https://example.com/profile for details")
    assert result["status"] == "pass"
    assert "liveness skipped" in result["details"]


# --- verbatim bullet check ---


def test_verbatim_bullet_check_flags_reuse():
    bullets = ["Cut cloud infrastructure costs by 35% through workload consolidation."]
    letter = "Some intro.\nCut cloud infrastructure costs by 35% through workload consolidation."
    assert factual.verbatim_bullet_check(letter, bullets)["status"] == "fail"


def test_verbatim_bullet_check_passes_when_complementary():
    bullets = ["Cut cloud infrastructure costs by 35% through workload consolidation."]
    letter = "I would bring the same cost discipline to your platform organization."
    assert factual.verbatim_bullet_check(letter, bullets)["status"] == "pass"


def test_verbatim_bullet_check_ignores_short_fragments():
    bullets = ["Python"]  # too short to count as a reused bullet
    assert factual.verbatim_bullet_check("I write Python daily.", bullets)["status"] == "pass"
