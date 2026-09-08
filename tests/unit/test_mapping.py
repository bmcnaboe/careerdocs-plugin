"""Tests for requirement-to-evidence mapping."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "skills" / "careerdocs" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from careerdocs import brief, diff, mapping, merge  # noqa: E402
from careerdocs.config import default_config  # noqa: E402
from careerdocs.providers import load_provider  # noqa: E402

CANDIDATES = json.loads((ROOT / "tests" / "fixtures" / "candidates.json").read_text())
JD = (ROOT / "examples" / "applicant" / "applications" / "example-role" / "job-description.md").read_text()


def built_profile(tmp_path):
    provider = load_provider(tmp_path, default_config())
    ops = merge.build_operations(provider.read(), CANDIDATES)
    d = diff.make_diff(provider, ops)
    diff.approve(provider, d["diff_id"])
    diff.apply(provider, d["diff_id"], cfg=default_config(), workspace=tmp_path)
    return provider.read()


def test_every_requirement_mapped_once(tmp_path):
    b = brief.generate_brief(JD)
    m = mapping.generate_map(b, built_profile(tmp_path))
    assert [e["requirement_id"] for e in m] == [r["id"] for r in b["requirements"]]


def test_fda_requirement_is_a_gap(tmp_path):
    b = brief.generate_brief(JD)
    profile = built_profile(tmp_path)
    m = mapping.generate_map(b, profile)
    fda_req = next(r for r in b["requirements"] if "FDA" in r["text"])
    entry = next(e for e in m if e["requirement_id"] == fda_req["id"])
    assert entry["classification"] == "gap"
    assert entry["evidence"] == []


def test_technical_requirements_are_direct(tmp_path):
    b = brief.generate_brief(JD)
    m = mapping.generate_map(b, built_profile(tmp_path))
    for keyword in ("Kubernetes", "Python"):
        req = next(r for r in b["requirements"] if keyword in r["text"])
        entry = next(e for e in m if e["requirement_id"] == req["id"])
        assert entry["classification"] == "direct"
        assert entry["evidence"]


def test_generated_map_validates(tmp_path):
    b = brief.generate_brief(JD)
    m = mapping.generate_map(b, built_profile(tmp_path))
    assert mapping.validate_map(m, b) == []


def test_validate_detects_missing_requirement(tmp_path):
    b = brief.generate_brief(JD)
    m = mapping.generate_map(b, built_profile(tmp_path))
    m.pop()  # drop one requirement's entry
    assert any("expected exactly one" in e for e in mapping.validate_map(m, b))


def test_validate_detects_gap_with_evidence(tmp_path):
    b = brief.generate_brief(JD)
    m = mapping.generate_map(b, built_profile(tmp_path))
    fda = next(e for e in m if e["classification"] == "gap")
    fda["evidence"] = [{"entity_id": "experience_x", "why": "spurious"}]
    assert any("gap must have no evidence" in e for e in mapping.validate_map(m, b))


def test_cli_map_writes_file(tmp_path, capsys):
    from careerdocs import cli

    ws = str(tmp_path)
    built_profile(tmp_path)  # profile now exists in the workspace
    app = tmp_path / "applications" / "example-role"
    app.mkdir(parents=True)
    (app / "brief.json").write_text(json.dumps(brief.generate_brief(JD)), encoding="utf-8")
    capsys.readouterr()
    assert cli.main(["map", "--role-slug", "example-role", "--workspace", ws, "--json"]) == 0
    out = json.loads(capsys.readouterr().out)
    written = json.loads(Path(out["map"]).read_text())
    assert out["counts"]["gap"] >= 1
    assert mapping.validate_map(written, brief.generate_brief(JD)) == []
