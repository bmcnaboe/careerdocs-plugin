"""Sanity checks that the example applicant fixtures are intact and sanitized."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "skills" / "careerdocs" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from careerdocs import config  # noqa: E402

APPLICANT = ROOT / "examples" / "applicant"
CANDIDATES = ROOT / "tests" / "fixtures" / "candidates.json"


def test_example_config_is_valid():
    data = json.loads((APPLICANT / "careerdocs.json").read_text())
    config.check_forbidden(data)
    config.validate_schema(data)


def test_binary_sources_exist():
    assert (APPLICANT / "sources" / "resume-a.docx").exists()
    assert (APPLICANT / "sources" / "resume-b.pdf").exists()


def test_text_sources_exist():
    for rel in ("sources/network-export.csv", "sources/voice-note.md", "voice/voice.md"):
        assert (APPLICANT / rel).exists()


def test_candidates_hold_the_deliberate_conflict():
    data = json.loads(CANDIDATES.read_text())
    globex = [
        c for c in data["candidates"]
        if c["type"] == "experience" and c["organization"] == "Globex Corporation"
    ]
    assert len(globex) == 2
    end_dates = {c["end_date"] for c in globex}
    assert end_dates == {"2021-06", "2021-08"}
    # The two candidates come from different sources.
    assert len({c["provenance"]["source_id"] for c in globex}) == 2


def test_voice_frontmatter_parses():
    text = (APPLICANT / "voice" / "voice.md").read_text()
    fenced = text.split("---", 2)[1]
    voice = json.loads(fenced)
    assert "banned_phrases" in voice and voice["person"] == "first"


def test_job_description_has_gap_requirement():
    jd = (APPLICANT / "applications" / "example-role" / "job-description.md").read_text()
    assert "FDA-cleared medical device" in jd
