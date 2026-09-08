"""install.sh: the zero-clone installer for Claude Code and Codex.

The script is driven end to end with a stub ``claude`` that records its arguments, a stub
``codex`` so Codex is detected, a temporary HOME, and the repository packed as the archive
the script would otherwise download from GitHub.
"""

from __future__ import annotations

import io
import json
import os
import re
import subprocess
import sys
import tarfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
INSTALL_SH = ROOT / "install.sh"
MANIFEST = json.loads((ROOT / "packages" / "openai" / "manifest.json").read_text(encoding="utf-8"))
SKILL_NAMES = [s["name"] for s in MANIFEST["skills"]]

CLAUDE_STUB = """#!/usr/bin/env bash
printf '%s\\n' "$*" >> "$CLAUDE_LOG"
case "$*" in
  "plugin marketplace list --json") cat "$CLAUDE_MARKETPLACES" ;;
  "plugin list --json") cat "$CLAUDE_PLUGINS" ;;
esac
"""


def build_archive(path: Path) -> None:
    """Pack skills/ and packages/ the way GitHub's archive does: under one top directory."""
    with tarfile.open(path, "w:gz") as tar:
        for member in ("skills", "packages"):
            tar.add(ROOT / member, arcname=f"careerdocs-plugin-main/{member}",
                    filter=lambda t: None if "__pycache__" in t.name else t)


class Harness:
    def __init__(self, tmp_path: Path, *, claude: bool = True, codex: bool = True):
        self.home = tmp_path / "home"
        self.home.mkdir()
        self.bin = tmp_path / "bin"
        self.bin.mkdir()
        self.log = tmp_path / "claude.log"
        self.marketplaces = tmp_path / "marketplaces.json"
        self.plugins = tmp_path / "plugins.json"
        self.marketplaces.write_text("[]", encoding="utf-8")
        self.plugins.write_text("[]", encoding="utf-8")
        self.archive = tmp_path / "archive.tar.gz"
        build_archive(self.archive)
        if claude:
            stub = self.bin / "claude"
            stub.write_text(CLAUDE_STUB, encoding="utf-8")
            stub.chmod(0o755)
        if codex:
            stub = self.bin / "codex"
            stub.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
            stub.chmod(0o755)

    def run(self, *args: str) -> subprocess.CompletedProcess:
        env = {
            "HOME": str(self.home),
            # Stubs first, then the interpreter running the tests, then the system tools the
            # script needs (curl, tar, mktemp, uname, sed, awk, grep). No uv on this PATH.
            "PATH": os.pathsep.join([str(self.bin), str(Path(sys.executable).parent), "/usr/bin", "/bin"]),
            "CLAUDE_LOG": str(self.log),
            "CLAUDE_MARKETPLACES": str(self.marketplaces),
            "CLAUDE_PLUGINS": str(self.plugins),
            "CAREERDOCS_ARCHIVE_URL": self.archive.as_uri(),
            "LC_ALL": "C.UTF-8",
        }
        return subprocess.run(["bash", str(INSTALL_SH), *args], env=env, capture_output=True, text=True)

    def calls(self) -> list[str]:
        return self.log.read_text(encoding="utf-8").splitlines() if self.log.exists() else []

    def skills_dir(self) -> Path:
        return self.home / ".agents" / "skills"

    def mark_installed(self) -> None:
        self.marketplaces.write_text(json.dumps([{"name": "careerdocs-plugin"}]), encoding="utf-8")
        self.plugins.write_text(json.dumps([{"id": "careerdocs@careerdocs-plugin", "scope": "user"}]), encoding="utf-8")


def test_skill_list_matches_the_openai_manifest():
    text = INSTALL_SH.read_text(encoding="utf-8")
    match = re.search(r"^SKILLS=\((.*)\)$", text, re.M)
    assert match, "install.sh must declare SKILLS=(...)"
    assert match.group(1).split() == SKILL_NAMES


def test_help_exits_zero(tmp_path):
    result = Harness(tmp_path).run("--help")
    assert result.returncode == 0
    assert "--dry-run" in result.stdout and "--uninstall" in result.stdout


def test_dry_run_changes_nothing(tmp_path):
    h = Harness(tmp_path)
    result = h.run("--dry-run")
    assert result.returncode == 0, result.stderr
    assert "would run: claude plugin marketplace add bmcnaboe/careerdocs-plugin" in result.stdout
    assert "would run: claude plugin install careerdocs@careerdocs-plugin --scope user" in result.stdout
    assert "nothing was changed" in result.stdout
    assert not h.skills_dir().exists()
    assert all(call.endswith("--json") for call in h.calls())


def test_installs_into_both_agents(tmp_path):
    h = Harness(tmp_path)
    result = h.run()
    assert result.returncode == 0, result.stderr
    assert "plugin marketplace add bmcnaboe/careerdocs-plugin" in h.calls()
    assert "plugin install careerdocs@careerdocs-plugin --scope user" in h.calls()
    for name in SKILL_NAMES:
        installed = h.skills_dir() / name / "SKILL.md"
        assert installed.is_file() and not installed.is_symlink()
        assert installed.read_bytes() == (ROOT / "skills" / name / "SKILL.md").read_bytes()
    assert "onboard my career documents" in result.stdout


def test_rerun_updates_instead_of_reinstalling(tmp_path):
    h = Harness(tmp_path)
    h.mark_installed()
    result = h.run()
    assert result.returncode == 0, result.stderr
    calls = h.calls()
    assert not any(call.startswith("plugin marketplace add") for call in calls)
    assert "plugin update careerdocs@careerdocs-plugin" in calls
    assert (h.skills_dir() / "careerdocs" / "SKILL.md").is_file()


def test_rerun_replaces_an_install_made_under_the_old_plugin_name(tmp_path):
    h = Harness(tmp_path)
    h.marketplaces.write_text(json.dumps([{"name": "careerdocs-plugin"}]), encoding="utf-8")
    h.plugins.write_text(json.dumps([{"id": "careerdocs-plugin@careerdocs-plugin", "scope": "user"}]), encoding="utf-8")
    result = h.run()
    assert result.returncode == 0, result.stderr
    calls = h.calls()
    removed = "plugin uninstall careerdocs-plugin@careerdocs-plugin --scope user"
    installed = "plugin install careerdocs@careerdocs-plugin --scope user"
    assert removed in calls and installed in calls
    assert calls.index(removed) < calls.index(installed)
    assert not any(call.startswith("plugin update") for call in calls)


def test_uninstall_removes_what_it_installed(tmp_path):
    h = Harness(tmp_path)
    assert h.run().returncode == 0
    foreign = h.skills_dir() / "onboard"
    foreign_note = "someone else's skill"
    (h.skills_dir() / "unrelated").mkdir()
    h.mark_installed()
    result = h.run("--uninstall")
    assert result.returncode == 0, result.stderr
    assert "plugin uninstall careerdocs@careerdocs-plugin --scope user" in h.calls()
    assert "plugin marketplace remove careerdocs-plugin" in h.calls()
    assert not any((h.skills_dir() / name).exists() for name in SKILL_NAMES)
    assert (h.skills_dir() / "unrelated").is_dir()
    del foreign, foreign_note


def test_uninstall_leaves_a_foreign_skill_of_the_same_name(tmp_path):
    h = Harness(tmp_path)
    foreign = h.skills_dir() / "onboard"
    foreign.mkdir(parents=True)
    (foreign / "SKILL.md").write_text("---\nname: onboard\n---\nnot ours\n", encoding="utf-8")
    result = h.run("--uninstall")
    assert result.returncode == 0, result.stderr
    assert foreign.is_dir()
    assert "not installed from careerdocs-plugin" in result.stderr


def test_only_codex_never_touches_claude(tmp_path):
    h = Harness(tmp_path)
    result = h.run("--only", "codex")
    assert result.returncode == 0, result.stderr
    assert h.calls() == []
    assert (h.skills_dir() / "careerdocs" / "SKILL.md").is_file()


def test_no_agent_detected_fails_with_guidance(tmp_path):
    h = Harness(tmp_path, claude=False, codex=False)
    result = h.run()
    assert result.returncode == 1
    assert "npx skills add bmcnaboe/careerdocs-plugin -g" in result.stdout


def test_bad_option_is_a_usage_error(tmp_path):
    result = Harness(tmp_path).run("--only", "cursor")
    assert result.returncode == 2
    assert "--only takes claude or codex" in result.stderr
