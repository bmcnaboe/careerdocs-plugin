"""Tests for the role brief builder and validator."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "skills" / "careerdocs" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from careerdocs import brief, cli  # noqa: E402

JD = (ROOT / "examples" / "applicant" / "applications" / "example-role" / "job-description.md")


def test_generate_brief_extracts_requirements():
    result = brief.generate_brief(JD.read_text())
    assert len(result["requirements"]) >= 4
    ids = [r["id"] for r in result["requirements"]]
    assert ids == [f"req-{i}" for i in range(1, len(ids) + 1)]


def test_must_and_nice_kinds_detected():
    result = brief.generate_brief(JD.read_text())
    kinds = {r["kind"] for r in result["requirements"]}
    assert "must" in kinds and "nice" in kinds
    fda = next(r for r in result["requirements"] if "FDA" in r["text"])
    assert fda["kind"] == "must"


def test_markers_stripped_from_text():
    result = brief.generate_brief(JD.read_text())
    assert all("(must)" not in r["text"] and "(nice)" not in r["text"] for r in result["requirements"])


def test_keywords_extracted():
    result = brief.generate_brief(JD.read_text())
    kubernetes = next(r for r in result["requirements"] if "Kubernetes" in r["text"])
    assert "kubernetes" in kubernetes["keywords"]


def test_positioning_recommended():
    assert brief.recommend_positioning(JD.read_text()) in ("executive", "builder")


def test_generated_brief_validates():
    result = brief.generate_brief(JD.read_text(), source=None)
    assert brief.validate_brief(result) == []


def test_validate_rejects_bad_positioning():
    result = brief.generate_brief(JD.read_text())
    result["recommended_positioning"] = "nonsense"
    assert brief.validate_brief(result)


def test_validate_rejects_duplicate_ids():
    result = brief.generate_brief(JD.read_text())
    result["requirements"][1]["id"] = result["requirements"][0]["id"]
    assert any("duplicate requirement id" in e for e in brief.validate_brief(result))


def test_cli_brief_writes_to_application(tmp_path, capsys):
    cli.main(["config", "init", "--workspace", str(tmp_path)])
    jd = tmp_path / "applications" / "example-role" / "job-description.md"
    jd.parent.mkdir(parents=True)
    jd.write_text(JD.read_text(), encoding="utf-8")
    capsys.readouterr()
    rc = cli.main(["brief", str(jd), "--workspace", str(tmp_path), "--json"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    written = json.loads(Path(out["brief"]).read_text())
    assert Path(out["brief"]).parent.name == "example-role"
    assert brief.validate_brief(written) == []


def test_cli_brief_validate_mode(tmp_path):
    cli.main(["config", "init", "--workspace", str(tmp_path)])
    good = tmp_path / "brief.json"
    good.write_text(json.dumps(brief.generate_brief(JD.read_text())), encoding="utf-8")
    assert cli.main(["brief", str(good), "--validate", "--workspace", str(tmp_path)]) == 0

    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"requirements": [], "recommended_positioning": "x"}), encoding="utf-8")
    assert cli.main(["brief", str(bad), "--validate", "--workspace", str(tmp_path)]) == 1


def test_keyword_coverage_reports_literal_presence():
    from careerdocs import brief as brief_module

    profile = {"entities": [
        {"type": "skill", "name": "Kubernetes", "visibility": "public", "verification": "applicant_verified"},
        {"type": "skill", "name": "Terraform", "visibility": "private", "verification": "applicant_verified"},
        {"type": "achievement", "statement": "Ran the platform team.", "visibility": "public", "verification": "applicant_verified"},
    ]}
    b = {"requirements": [
        {"id": "req-1", "text": "", "kind": "must", "keywords": ["kubernetes", "terraform"]},
        {"id": "req-2", "text": "", "kind": "nice", "keywords": ["platform", "kubernetes"]},
    ], "recommended_positioning": "builder"}
    rows = {row["keyword"]: row for row in brief_module.keyword_coverage(b, profile)}
    assert rows["kubernetes"]["present"] and rows["kubernetes"]["requirement_ids"] == ["req-1", "req-2"]
    assert rows["platform"]["present"]
    assert not rows["terraform"]["present"]  # private entities do not count
