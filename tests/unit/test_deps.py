"""Tests for the first-run dependency bootstrap (no real installs: every process call is stubbed)."""

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "skills" / "careerdocs" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from careerdocs import deps  # noqa: E402

ENTRY = str(SCRIPTS / "careerdocs.py")


class Exec(Exception):
    """Stands in for exec*, which never returns."""


@pytest.fixture
def calls(monkeypatch):
    record = {"exec": None, "runs": []}

    def fake_execvpe(file, args, env):
        record["exec"] = ("execvpe", file, args, env)
        raise Exec

    def fake_execve(path, args, env):
        record["exec"] = ("execve", path, args, env)
        raise Exec

    monkeypatch.setattr(deps.os, "execvpe", fake_execvpe)
    monkeypatch.setattr(deps.os, "execve", fake_execve)
    monkeypatch.delenv(deps.BOOTSTRAPPED, raising=False)
    return record


def test_status_covers_every_runtime_dependency():
    assert set(deps.status()) == set(deps.RUNTIME_DEPENDENCIES)
    assert deps.missing() == []  # the test environment has them all


def test_ensure_is_a_no_op_when_nothing_is_missing(calls):
    deps.ensure(ENTRY, ["version"])
    assert calls["exec"] is None


def test_reexecs_under_uv_when_available(calls, monkeypatch):
    monkeypatch.setattr(deps, "missing", lambda: ["docxtpl"])
    monkeypatch.setattr(deps.shutil, "which", lambda name: "/usr/local/bin/uv")
    with pytest.raises(Exec):
        deps.ensure(ENTRY, ["doctor", "--json"])
    kind, file, args, env = calls["exec"]
    assert (kind, file) == ("execvpe", "uv")
    assert args == ["uv", "run", "--quiet", ENTRY, "doctor", "--json"]
    assert env[deps.BOOTSTRAPPED] == "1"


def test_installs_with_pip_then_reexecs_itself(calls, monkeypatch):
    monkeypatch.setattr(deps, "missing", lambda: ["docxtpl", "pypdf"])
    monkeypatch.setattr(deps.shutil, "which", lambda name: None)
    monkeypatch.setattr(deps, "in_virtualenv", lambda: False)

    def fake_run(cmd, **kwargs):
        calls["runs"].append(cmd)
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(deps.subprocess, "run", fake_run)
    with pytest.raises(Exec):
        deps.ensure(ENTRY, ["version"])
    assert calls["runs"] == [[sys.executable, "-m", "pip", "install", "--quiet", "docxtpl", "pypdf", "--user"]]
    kind, path, args, env = calls["exec"]
    assert (kind, path, args) == ("execve", sys.executable, [sys.executable, ENTRY, "version"])
    assert env[deps.BOOTSTRAPPED] == "1"


def test_inside_a_virtualenv_pip_installs_without_user(monkeypatch):
    monkeypatch.setattr(deps, "in_virtualenv", lambda: True)
    assert "--user" not in deps.pip_install_command(["jsonschema"])


def test_retries_with_break_system_packages_when_pip_refuses(calls, monkeypatch):
    monkeypatch.setattr(deps, "missing", lambda: ["jsonschema"])
    monkeypatch.setattr(deps.shutil, "which", lambda name: None)
    monkeypatch.setattr(deps, "in_virtualenv", lambda: False)

    def fake_run(cmd, **kwargs):
        calls["runs"].append(cmd)
        if "--break-system-packages" in cmd:
            return subprocess.CompletedProcess(cmd, 0, "", "")
        return subprocess.CompletedProcess(cmd, 1, "", "error: externally-managed-environment")

    monkeypatch.setattr(deps.subprocess, "run", fake_run)
    with pytest.raises(Exec):
        deps.ensure(ENTRY, ["version"])
    assert len(calls["runs"]) == 2 and calls["runs"][1][-1] == "--break-system-packages"


def test_pip_failure_exits_two_with_the_command_to_run(calls, monkeypatch, capsys):
    monkeypatch.setattr(deps, "missing", lambda: ["pdfplumber"])
    monkeypatch.setattr(deps.shutil, "which", lambda name: None)
    monkeypatch.setattr(
        deps.subprocess, "run",
        lambda cmd, **kw: subprocess.CompletedProcess(cmd, 1, "", "ERROR: No matching distribution"),
    )
    with pytest.raises(SystemExit) as excinfo:
        deps.ensure(ENTRY, ["version"])
    assert excinfo.value.code == 2
    err = capsys.readouterr().err
    assert "pip install" in err and "No matching distribution" in err
    assert calls["exec"] is None


def test_never_loops_after_a_bootstrap_that_did_not_help(calls, monkeypatch, capsys):
    monkeypatch.setenv(deps.BOOTSTRAPPED, "1")
    monkeypatch.setattr(deps, "missing", lambda: ["docxtpl"])
    monkeypatch.setattr(deps.shutil, "which", lambda name: "/usr/local/bin/uv")
    with pytest.raises(SystemExit) as excinfo:
        deps.ensure(ENTRY, ["version"])
    assert excinfo.value.code == 2
    assert "still missing" in capsys.readouterr().err
    assert calls["exec"] is None
