"""Tests for the careerdocs CLI entry point and its always-present commands."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "skills" / "career-documents" / "scripts"
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


def test_doctor_sees_config(tmp_path, capsys):
    (tmp_path / "career-documents.json").write_text("{}", encoding="utf-8")
    assert cli.main(["doctor", "--workspace", str(tmp_path), "--json"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["config_present"] is True


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
