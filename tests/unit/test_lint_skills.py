"""Tests for the Agent Skills linter."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import lint_skills  # noqa: E402

GOOD_FRONTMATTER = """\
---
name: {name}
description: A valid description of the skill.
license: MIT
compatibility: "Python 3.11+, uv recommended"
metadata:
  version: "0.1.0"
  author: "career-documents contributors"
---

# Body

Some content.
"""


def make_skill(base: Path, name: str, *, frontmatter: str | None = None) -> Path:
    skill = base / name
    skill.mkdir(parents=True)
    body = frontmatter if frontmatter is not None else GOOD_FRONTMATTER.format(name=name)
    (skill / "SKILL.md").write_text(body, encoding="utf-8")
    return skill


def test_valid_skill_has_no_errors(tmp_path):
    make_skill(tmp_path, "career-onboard")
    assert lint_skills.lint_all(tmp_path) == []


def test_name_must_match_directory(tmp_path):
    make_skill(tmp_path, "career-onboard",
               frontmatter=GOOD_FRONTMATTER.format(name="something-else"))
    errors = lint_skills.lint_all(tmp_path)
    assert any("does not match directory" in e for e in errors)


def test_name_rejects_uppercase(tmp_path):
    assert any("lowercase" in e for e in lint_skills.name_errors("Career", "Career"))


def test_name_rejects_leading_and_doubled_hyphen(tmp_path):
    assert any("start or end" in e for e in lint_skills.name_errors("-x", "-x"))
    assert any("doubled hyphen" in e for e in lint_skills.name_errors("a--b", "a--b"))


def test_name_length_bound(tmp_path):
    long = "a" * 65
    assert any("1-64" in e for e in lint_skills.name_errors(long, long))


def test_missing_description(tmp_path):
    fm = "---\nname: career-onboard\n---\n\nbody\n"
    make_skill(tmp_path, "career-onboard", frontmatter=fm)
    assert any("missing 'description'" in e for e in lint_skills.lint_all(tmp_path))


def test_description_too_long(tmp_path):
    desc = "x" * 1025
    fm = f"---\nname: career-onboard\ndescription: {desc}\n---\n\nbody\n"
    make_skill(tmp_path, "career-onboard", frontmatter=fm)
    assert any("description exceeds" in e for e in lint_skills.lint_all(tmp_path))


def test_body_too_long(tmp_path):
    body = "\n".join(f"line {i}" for i in range(501))
    fm = f"---\nname: career-onboard\ndescription: ok\n---\n{body}\n"
    make_skill(tmp_path, "career-onboard", frontmatter=fm)
    assert any("body is" in e for e in lint_skills.lint_all(tmp_path))


def test_missing_frontmatter(tmp_path):
    make_skill(tmp_path, "career-onboard", frontmatter="# no frontmatter here\n")
    assert any("frontmatter fence" in e for e in lint_skills.lint_all(tmp_path))


def test_missing_skill_md(tmp_path):
    (tmp_path / "career-onboard").mkdir()
    assert any("missing SKILL.md" in e for e in lint_skills.lint_all(tmp_path))


def test_openai_yaml_must_be_flat(tmp_path):
    skill = make_skill(tmp_path, "career-onboard")
    agents = skill / "agents"
    agents.mkdir()
    (agents / "openai.yaml").write_text(
        "name: Career Onboard\nnested:\n  bad: value\n", encoding="utf-8"
    )
    assert any("must be flat" in e for e in lint_skills.lint_all(tmp_path))


def test_openai_yaml_flat_ok(tmp_path):
    skill = make_skill(tmp_path, "career-onboard")
    agents = skill / "agents"
    agents.mkdir()
    (agents / "openai.yaml").write_text(
        "name: Career Onboard\nallow_implicit_invocation: true\n", encoding="utf-8"
    )
    assert lint_skills.lint_all(tmp_path) == []


def test_parse_frontmatter_reads_metadata_map():
    data, body = lint_skills.parse_frontmatter(GOOD_FRONTMATTER.format(name="career-onboard"))
    assert data["metadata"]["version"] == "0.1.0"
    assert data["name"] == "career-onboard"
    assert any("Body" in line for line in body)


def test_missing_skills_dir_is_clean(tmp_path):
    assert lint_skills.lint_all(tmp_path / "does-not-exist") == []


def test_repo_skills_lint_clean():
    # Whatever skills exist in the repo must already pass.
    assert lint_skills.lint_all(ROOT / "skills") == []
