"""Tests for render history: git commits in a versioned workspace, the archive otherwise."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "skills" / "careerdocs" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from careerdocs import cli, history  # noqa: E402
from careerdocs.config import default_config  # noqa: E402
from careerdocs.errors import CareerDocsError  # noqa: E402


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True).stdout.strip()


def init_repo(path):
    subprocess.run(["git", "init", "-q", str(path)], check=True)
    git(path, "config", "user.name", "Test")
    git(path, "config", "user.email", "test@example.com")


def test_no_repository_means_archive(tmp_path):
    assert history.repository(tmp_path) is None
    assert history.mode(tmp_path, default_config()) == "archive"


def test_mode_honors_the_setting(tmp_path, tmp_path_factory):
    init_repo(tmp_path)
    cfg = default_config()
    assert history.mode(tmp_path, cfg) == "git"
    assert history.repository(tmp_path / "applications") is None or history.repository(tmp_path) == tmp_path.resolve()
    cfg["outputs"]["history"] = "archive"
    assert history.mode(tmp_path, cfg) == "archive"
    plain = tmp_path_factory.mktemp("plain")
    cfg["outputs"]["history"] = "git"
    with pytest.raises(CareerDocsError):
        history.mode(plain, cfg)


def test_changed_and_commit_touch_only_the_named_paths(tmp_path):
    init_repo(tmp_path)
    app = tmp_path / "applications" / "role"
    app.mkdir(parents=True)
    (app / "brief.json").write_text("{}", encoding="utf-8")
    (tmp_path / "unrelated.txt").write_text("x", encoding="utf-8")

    assert history.changed(tmp_path, [app]) == [(tmp_path / "applications" / "role" / "brief.json").resolve()]
    sha = history.commit(tmp_path, [app], "feat(role): first")
    assert sha and git(tmp_path, "log", "--format=%s") == "feat(role): first"
    # The unrelated file was neither staged nor committed.
    assert git(tmp_path, "status", "--porcelain") == "?? unrelated.txt"
    # Nothing changed under the paths: no commit.
    assert history.commit(tmp_path, [app], "again") is None
    (app / "brief.json").write_text('{"a": 1}', encoding="utf-8")
    assert history.commit(tmp_path, [app], "fix(role): brief") is not None
    assert git(tmp_path, "rev-list", "--count", "HEAD") == "2"


def test_round_paths_cover_the_application_its_state_and_the_profile(tmp_path):
    cfg = default_config()
    state = tmp_path / ".careerdocs" / "state" / "apply"
    state.mkdir(parents=True)
    (state / "role.json").write_text("{}", encoding="utf-8")
    paths = history.round_paths(tmp_path, cfg, slug="role", extra=["templates"])
    assert paths == [tmp_path / "applications" / "role", state / "role.json", tmp_path / "profile", tmp_path / "templates"]
    baseline = history.round_paths(tmp_path, cfg, baseline="builder")
    assert baseline == [tmp_path / "baselines" / "builder", tmp_path / "profile"]


def test_commit_command_is_a_no_op_without_git(tmp_path, capsys):
    cli.main(["config", "init", "--workspace", str(tmp_path)])
    capsys.readouterr()
    assert cli.main(["commit", "--role-slug", "role", "-m", "feat(role): x", "--workspace", str(tmp_path), "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"history": "archive", "committed": None}


def test_commit_command_commits_a_round(tmp_path, capsys):
    init_repo(tmp_path)
    cli.main(["config", "init", "--workspace", str(tmp_path)])
    app = tmp_path / "applications" / "role"
    app.mkdir(parents=True)
    (app / "brief.json").write_text("{}", encoding="utf-8")
    capsys.readouterr()
    assert cli.main(["commit", "--role-slug", "role", "-m", "feat(role): brief", "--workspace", str(tmp_path), "--json"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["history"] == "git" and out["committed"]
    assert git(tmp_path, "log", "--format=%s") == "feat(role): brief"
    # careerdocs.json was not part of the round, so it stays uncommitted until named.
    assert "careerdocs.json" in git(tmp_path, "status", "--porcelain")
    capsys.readouterr()
    assert cli.main(["commit", "--path", "careerdocs.json", "-m", "chore: configure the workspace", "--workspace", str(tmp_path), "--json"]) == 0
    assert git(tmp_path, "status", "--porcelain") == ""


def test_commit_command_requires_a_scope(tmp_path):
    cli.main(["config", "init", "--workspace", str(tmp_path)])
    assert cli.main(["commit", "-m", "x", "--workspace", str(tmp_path)]) == 2
