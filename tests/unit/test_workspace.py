"""Tests for workspace resolution: flag, environment, marker file, recorded default, cwd."""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "skills" / "careerdocs" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from careerdocs import cli, workspace  # noqa: E402
from careerdocs.errors import WorkspaceError  # noqa: E402


@pytest.fixture
def cwd(tmp_path, monkeypatch):
    """An empty current directory with no careerdocs.json anywhere above it."""
    here = tmp_path / "cwd"
    here.mkdir()
    monkeypatch.chdir(here)
    return here


def test_flag_wins_over_everything(tmp_path, cwd, monkeypatch):
    monkeypatch.setenv(workspace.ENV_VAR, str(tmp_path / "from-env"))
    located = workspace.resolve(str(tmp_path / "flag"))
    assert located.source == "flag"
    assert located.path == (tmp_path / "flag").resolve()


def test_environment_wins_over_marker(tmp_path, cwd, monkeypatch):
    (cwd / "careerdocs.json").write_text("{}", encoding="utf-8")
    monkeypatch.setenv(workspace.ENV_VAR, str(tmp_path / "from-env"))
    located = workspace.resolve()
    assert located.source == "env"
    assert located.path == (tmp_path / "from-env").resolve()


def test_marker_is_found_in_a_parent(cwd, monkeypatch):
    (cwd / "careerdocs.json").write_text("{}", encoding="utf-8")
    sub = cwd / "applications" / "role"
    sub.mkdir(parents=True)
    monkeypatch.chdir(sub)
    located = workspace.resolve()
    assert located.source == "marker"
    assert located.path == cwd.resolve()
    assert located.established


def test_recorded_default_is_used_when_nothing_else_applies(tmp_path, cwd):
    default = tmp_path / "default"
    default.mkdir()
    pointer = workspace.write_pointer(default)
    assert pointer == Path(tmp_path / ".config" / "careerdocs" / "workspace")
    located = workspace.resolve()
    assert located.source == "pointer"
    assert located.path == default.resolve()


def test_recorded_default_that_is_missing_is_an_error(tmp_path, cwd, capsys):
    workspace.write_pointer(tmp_path / "gone")
    with pytest.raises(WorkspaceError):
        workspace.resolve()
    assert cli.main(["profile", "status"]) == 2
    assert "WORKSPACE_UNRESOLVED" in capsys.readouterr().err


def test_bare_cwd_is_unestablished(cwd):
    located = workspace.resolve()
    assert located.source == "cwd"
    assert located.path == cwd.resolve()
    assert not located.established
    with pytest.raises(WorkspaceError):
        workspace.ensure_established(located)


def test_data_commands_refuse_a_bare_cwd(cwd, capsys):
    assert cli.main(["profile", "status"]) == 2
    err = capsys.readouterr().err
    assert "WORKSPACE_UNRESOLVED" in err and "config workspace" in err
    assert not any(cwd.iterdir())


def test_setup_commands_run_in_a_bare_cwd(cwd, capsys):
    assert cli.main(["doctor", "--json"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["workspace_source"] == "cwd"
    assert cli.main(["config", "init"]) == 0
    capsys.readouterr()
    # The marker now establishes the directory, so data commands work.
    assert cli.main(["profile", "status", "--json"]) == 0


def test_doctor_names_the_source(cwd, capsys):
    assert cli.main(["doctor"]) == 0
    assert "(via the current directory" in capsys.readouterr().out


def test_config_workspace_records_creates_and_initializes(tmp_path, cwd, capsys):
    target = tmp_path / "chosen"
    assert cli.main(["config", "workspace", str(target), "--json"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["created"] is True
    assert (target / "careerdocs.json").is_file()
    assert Path(result["pointer"]).read_text(encoding="utf-8").strip() == str(target.resolve())
    # From now on, any directory resolves to it.
    assert cli.main(["config", "workspace", "--json"]) == 0
    shown = json.loads(capsys.readouterr().out)
    assert shown == {
        "workspace": str(target.resolve()),
        "source": "pointer",
        "established": True,
        "pointer": result["pointer"],
    }


def test_config_workspace_expands_tilde(tmp_path, cwd, monkeypatch, capsys):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    assert cli.main(["config", "workspace", "~/career", "--json"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["workspace"] == str((tmp_path / "home" / "career").resolve())


def test_config_workspace_is_idempotent(tmp_path, cwd, capsys):
    target = tmp_path / "chosen"
    assert cli.main(["config", "workspace", str(target)]) == 0
    capsys.readouterr()
    assert cli.main(["config", "workspace", str(target)]) == 0
    assert "already present" in capsys.readouterr().out
