"""Tests for the careerdocs CLI entry point and its always-present commands."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "skills" / "careerdocs" / "scripts"
ENTRY = SCRIPTS / "careerdocs.py"
sys.path.insert(0, str(SCRIPTS))

from careerdocs import __version__, cli  # noqa: E402


def test_version_human(capsys):
    assert cli.main(["version"]) == 0
    out = capsys.readouterr().out
    assert f"careerdocs {__version__}" in out
    assert "profile schema" in out


def test_version_json(capsys):
    assert cli.main(["version", "--json"]) == 0
    info = json.loads(capsys.readouterr().out)
    assert info["careerdocs"] == __version__
    assert info["profile_schema"].count(".") == 2


def test_doctor_json_reports_status(tmp_path, capsys):
    assert cli.main(["doctor", "--workspace", str(tmp_path), "--json"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["config_present"] is False
    assert "soffice" in report["converter"]
    assert "jsonschema" in report["dependencies"]
    # With no config, defaults apply: markdown provider reachable with an empty profile.
    assert report["provider"]["authoritative"] == "markdown"
    assert report["provider"]["reachable"] is True
    assert report["provider"]["entities"] == 0
    assert report["templates"] == {"resume": False, "cover_letter": False}
    assert report["voice"]["present"] is False


def test_doctor_sees_config(tmp_path, capsys):
    cli.main(["config", "init", "--workspace", str(tmp_path)])
    capsys.readouterr()
    assert cli.main(["doctor", "--workspace", str(tmp_path), "--json"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["config_present"] is True
    assert report["config_valid"] is True


def test_doctor_detects_templates_and_voice(tmp_path, capsys):
    cli.main(["config", "init", "--workspace", str(tmp_path)])
    (tmp_path / "templates" / "resume").mkdir(parents=True)
    (tmp_path / "templates" / "resume" / "template.docx").write_bytes(b"stub")
    (tmp_path / "voice").mkdir()
    (tmp_path / "voice" / "voice.md").write_text("---\n{}\n---\n", encoding="utf-8")
    capsys.readouterr()
    assert cli.main(["doctor", "--workspace", str(tmp_path), "--json"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["templates"]["resume"] is True
    assert report["voice"]["present"] is True


def test_doctor_reports_invalid_config(tmp_path, capsys):
    (tmp_path / "careerdocs.json").write_text('{"version": "1", "api_key": "x"}', encoding="utf-8")
    assert cli.main(["doctor", "--workspace", str(tmp_path), "--json"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["config_valid"] is False
    assert report["config_error"]


def test_unknown_command_is_usage_error():
    with pytest.raises(SystemExit) as excinfo:
        cli.main(["nonesuch"])
    assert excinfo.value.code == 2


def test_no_command_is_usage_error():
    with pytest.raises(SystemExit) as excinfo:
        cli.main([])
    assert excinfo.value.code == 2


def test_entry_point_runs_as_script():
    result = subprocess.run(
        [sys.executable, str(ENTRY), "version", "--json"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert json.loads(result.stdout)["careerdocs"] == __version__


def test_doctor_advises_on_non_standard_section_titles(tmp_path, capsys):
    cli.main(["config", "init", "--workspace", str(tmp_path)])
    manifest = tmp_path / "templates" / "resume" / "template.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(json.dumps({"sections": [
        {"id": "experience", "title": "Experience"}, {"id": "skills", "title": "Technical Focus"}]}), encoding="utf-8")
    capsys.readouterr()
    assert cli.main(["doctor", "--workspace", str(tmp_path), "--json"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert len(report["advisories"]) == 1 and "Technical Focus" in report["advisories"][0]
