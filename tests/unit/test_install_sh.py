"""install.sh: the zero-clone installer for Claude Code and Codex.

The script is driven end to end with a stub ``claude`` and a stub ``codex`` that record
their arguments and mimic what the real plugin managers leave behind (a cached copy of the
plugin, here a link to this repository), plus a temporary HOME.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INSTALL_SH = ROOT / "install.sh"
SKILL_NAMES = sorted(d.name for d in (ROOT / "skills").iterdir() if (d / "SKILL.md").is_file())
LEGACY_MARKER = "careerdocs-plugin contributors"

CLAUDE_STUB = """#!/usr/bin/env bash
printf '%s\\n' "$*" >> "$CLAUDE_LOG"
case "$*" in
  "plugin marketplace list --json") cat "$CLAUDE_MARKETPLACES" ;;
  "plugin list --json") cat "$CLAUDE_PLUGINS" ;;
  "plugin install careerdocs@careerdocs-plugin --scope user"|"plugin update careerdocs@careerdocs-plugin")
    mkdir -p "$HOME/.claude/plugins/cache/careerdocs-plugin/careerdocs"
    ln -sfn "$REPO_ROOT" "$HOME/.claude/plugins/cache/careerdocs-plugin/careerdocs/0.1.0" ;;
esac
"""

CODEX_STUB = """#!/usr/bin/env bash
printf '%s\\n' "$*" >> "$CODEX_LOG"
case "$*" in
  "--version") echo "codex-cli 0.153.4" ;;
  "plugin --help") exit "${CODEX_NO_PLUGINS:-0}" ;;
  "plugin marketplace list") cat "$CODEX_MARKETPLACES" ;;
  "plugin list") cat "$CODEX_PLUGINS" ;;
  "plugin marketplace add "*) printf 'careerdocs-plugin  /marketplace\\n' > "$CODEX_MARKETPLACES" ;;
  "plugin add careerdocs@careerdocs-plugin")
    mkdir -p "$HOME/.codex/plugins/cache/careerdocs-plugin/careerdocs"
    ln -sfn "$REPO_ROOT" "$HOME/.codex/plugins/cache/careerdocs-plugin/careerdocs/0.1.0"
    printf 'careerdocs@careerdocs-plugin  installed, enabled  0.1.0  /marketplace\\n' > "$CODEX_PLUGINS" ;;
  "plugin remove careerdocs@careerdocs-plugin")
    : > "$CODEX_PLUGINS"; rm -rf "$HOME/.codex/plugins/cache/careerdocs-plugin" ;;
  "plugin marketplace remove careerdocs-plugin") : > "$CODEX_MARKETPLACES" ;;
esac
"""


class Harness:
    def __init__(self, tmp_path: Path, *, claude: bool = True, codex: bool = True):
        self.home = tmp_path / "home"
        self.home.mkdir()
        self.bin = tmp_path / "bin"
        self.bin.mkdir()
        self.claude_log = tmp_path / "claude.log"
        self.codex_log = tmp_path / "codex.log"
        self.claude_marketplaces = tmp_path / "claude-marketplaces.json"
        self.claude_plugins = tmp_path / "claude-plugins.json"
        self.codex_marketplaces = tmp_path / "codex-marketplaces.txt"
        self.codex_plugins = tmp_path / "codex-plugins.txt"
        self.claude_marketplaces.write_text("[]", encoding="utf-8")
        self.claude_plugins.write_text("[]", encoding="utf-8")
        self.codex_marketplaces.write_text("", encoding="utf-8")
        self.codex_plugins.write_text("", encoding="utf-8")
        if claude:
            self._stub("claude", CLAUDE_STUB)
        if codex:
            self._stub("codex", CODEX_STUB)

    def _stub(self, name: str, body: str) -> None:
        stub = self.bin / name
        stub.write_text(body, encoding="utf-8")
        stub.chmod(0o755)

    def run(self, *args: str, env: dict | None = None) -> subprocess.CompletedProcess:
        environment = {
            "HOME": str(self.home),
            # Stubs first, then the interpreter running the tests, then the system tools the
            # script needs (uname, sed, awk, grep, ls). No uv on this PATH.
            "PATH": os.pathsep.join([str(self.bin), str(Path(sys.executable).parent), "/usr/bin", "/bin"]),
            "REPO_ROOT": str(ROOT),
            "CLAUDE_LOG": str(self.claude_log),
            "CLAUDE_MARKETPLACES": str(self.claude_marketplaces),
            "CLAUDE_PLUGINS": str(self.claude_plugins),
            "CODEX_LOG": str(self.codex_log),
            "CODEX_MARKETPLACES": str(self.codex_marketplaces),
            "CODEX_PLUGINS": str(self.codex_plugins),
            "LC_ALL": "C.UTF-8",
            **(env or {}),
        }
        return subprocess.run(["bash", str(INSTALL_SH), *args], env=environment, capture_output=True, text=True)

    def claude_calls(self) -> list[str]:
        return self.claude_log.read_text(encoding="utf-8").splitlines() if self.claude_log.exists() else []

    def codex_calls(self) -> list[str]:
        return self.codex_log.read_text(encoding="utf-8").splitlines() if self.codex_log.exists() else []

    def claude_cache(self) -> Path:
        return self.home / ".claude" / "plugins" / "cache" / "careerdocs-plugin" / "careerdocs" / "0.1.0"

    def codex_cache(self) -> Path:
        return self.home / ".codex" / "plugins" / "cache" / "careerdocs-plugin" / "careerdocs" / "0.1.0"

    def legacy_skills_dir(self) -> Path:
        return self.home / ".agents" / "skills"

    def pointer(self) -> Path:
        return self.home / ".config" / "careerdocs" / "workspace"

    def add_legacy_copy(self, name: str, *, ours: bool = True) -> Path:
        """A skill folder under ~/.agents/skills, as an earlier installer (or someone else) left it."""
        folder = self.legacy_skills_dir() / name
        folder.mkdir(parents=True)
        author = LEGACY_MARKER if ours else "someone else"
        (folder / "SKILL.md").write_text(f"---\nname: {name}\nmetadata:\n  author: \"{author}\"\n---\n", encoding="utf-8")
        return folder

    def mark_installed(self) -> None:
        self.claude_marketplaces.write_text(json.dumps([{"name": "careerdocs-plugin"}]), encoding="utf-8")
        self.claude_plugins.write_text(json.dumps([{"id": "careerdocs@careerdocs-plugin", "scope": "user"}]), encoding="utf-8")
        self.codex_marketplaces.write_text("careerdocs-plugin  /marketplace\n", encoding="utf-8")
        self.codex_plugins.write_text("careerdocs@careerdocs-plugin  installed, enabled  0.1.0  /marketplace\n", encoding="utf-8")
        for cache in (self.claude_cache(), self.codex_cache()):
            cache.parent.mkdir(parents=True, exist_ok=True)
            if not cache.is_symlink():
                cache.symlink_to(ROOT)


def test_skill_list_matches_the_skills_tree():
    text = INSTALL_SH.read_text(encoding="utf-8")
    match = re.search(r"^SKILLS=\((.*)\)$", text, re.M)
    assert match, "install.sh must declare SKILLS=(...)"
    assert sorted(match.group(1).split()) == SKILL_NAMES


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
    assert "would run: codex plugin marketplace add bmcnaboe/careerdocs-plugin" in result.stdout
    assert "would run: codex plugin add careerdocs@careerdocs-plugin" in result.stdout
    assert "would ask for the workspace folder" in result.stdout
    assert "nothing was changed" in result.stdout
    assert not (h.home / ".claude").exists() and not (h.home / ".codex").exists()
    assert all(call.endswith("--json") for call in h.claude_calls())
    assert not any(call.startswith(("plugin add", "plugin marketplace add")) for call in h.codex_calls())


def test_installs_into_both_agents_through_their_plugin_managers(tmp_path):
    h = Harness(tmp_path)
    result = h.run()
    assert result.returncode == 0, result.stderr
    assert "plugin marketplace add bmcnaboe/careerdocs-plugin" in h.claude_calls()
    assert "plugin install careerdocs@careerdocs-plugin --scope user" in h.claude_calls()
    assert "plugin marketplace add bmcnaboe/careerdocs-plugin" in h.codex_calls()
    assert "plugin add careerdocs@careerdocs-plugin" in h.codex_calls()
    assert h.claude_cache().is_symlink() and h.codex_cache().is_symlink()
    # The script copies nothing itself: no skills land outside the plugin managers' caches.
    assert not h.legacy_skills_dir().exists()
    # Not a terminal and no --workspace: nothing is recorded, and the guidance says so.
    assert not h.pointer().exists()
    assert "no workspace folder was chosen" in result.stdout
    assert "/careerdocs:onboard" in result.stdout and "$onboard" in result.stdout
    assert "Add marketplace > bmcnaboe/careerdocs-plugin" in result.stdout
    # The steps themselves live in the onboard skill, not in the script's output.
    assert "LinkedIn" not in result.stdout and "/careerdocs:resume" not in result.stdout


def test_rerun_updates_instead_of_reinstalling(tmp_path):
    h = Harness(tmp_path)
    h.mark_installed()
    result = h.run()
    assert result.returncode == 0, result.stderr
    assert not any(call.startswith("plugin marketplace add") for call in h.claude_calls())
    assert "plugin marketplace update careerdocs-plugin" in h.claude_calls()
    assert "plugin update careerdocs@careerdocs-plugin" in h.claude_calls()
    assert not any(call.startswith("plugin marketplace add") for call in h.codex_calls())
    assert "plugin marketplace upgrade careerdocs-plugin" in h.codex_calls()
    assert "plugin add careerdocs@careerdocs-plugin" in h.codex_calls()
    assert "refreshed marketplace careerdocs-plugin" in result.stdout


def test_rerun_replaces_an_install_made_under_the_old_plugin_name(tmp_path):
    h = Harness(tmp_path)
    h.claude_marketplaces.write_text(json.dumps([{"name": "careerdocs-plugin"}]), encoding="utf-8")
    h.claude_plugins.write_text(json.dumps([{"id": "careerdocs-plugin@careerdocs-plugin", "scope": "user"}]), encoding="utf-8")
    result = h.run()
    assert result.returncode == 0, result.stderr
    calls = h.claude_calls()
    removed = "plugin uninstall careerdocs-plugin@careerdocs-plugin --scope user"
    installed = "plugin install careerdocs@careerdocs-plugin --scope user"
    assert removed in calls and installed in calls
    assert calls.index(removed) < calls.index(installed)
    assert not any(call.startswith("plugin update") for call in calls)


def test_ref_is_passed_to_both_marketplaces(tmp_path):
    h = Harness(tmp_path)
    result = h.run("--ref", "v1.2.0")
    assert result.returncode == 0, result.stderr
    assert "plugin marketplace add https://github.com/bmcnaboe/careerdocs-plugin.git#v1.2.0" in h.claude_calls()
    assert "plugin marketplace add bmcnaboe/careerdocs-plugin@v1.2.0" in h.codex_calls()


def test_legacy_codex_copies_are_removed_on_install(tmp_path):
    h = Harness(tmp_path)
    ours = h.add_legacy_copy("onboard")
    foreign = h.add_legacy_copy("update", ours=False)
    (h.legacy_skills_dir() / "unrelated").mkdir()
    result = h.run()
    assert result.returncode == 0, result.stderr
    assert not ours.exists()
    assert foreign.is_dir() and (h.legacy_skills_dir() / "unrelated").is_dir()
    assert "earlier version of this script" in result.stdout
    assert "not installed from careerdocs-plugin" in result.stderr


def test_codex_without_plugin_commands_is_skipped_with_guidance(tmp_path):
    h = Harness(tmp_path)
    result = h.run(env={"CODEX_NO_PLUGINS": "1"})
    assert result.returncode == 0, result.stderr
    assert "has no plugin commands" in result.stderr
    assert not any(call.startswith("plugin add") for call in h.codex_calls())
    assert "plugin install careerdocs@careerdocs-plugin --scope user" in h.claude_calls()


def test_uninstall_removes_what_it_installed(tmp_path):
    h = Harness(tmp_path)
    h.mark_installed()
    ours = h.add_legacy_copy("resume")
    result = h.run("--uninstall")
    assert result.returncode == 0, result.stderr
    assert "plugin uninstall careerdocs@careerdocs-plugin --scope user" in h.claude_calls()
    assert "plugin marketplace remove careerdocs-plugin" in h.claude_calls()
    assert "plugin remove careerdocs@careerdocs-plugin" in h.codex_calls()
    assert "plugin marketplace remove careerdocs-plugin" in h.codex_calls()
    assert not h.codex_cache().exists() and not ours.exists()


def test_uninstall_leaves_a_foreign_skill_of_the_same_name(tmp_path):
    h = Harness(tmp_path)
    foreign = h.add_legacy_copy("onboard", ours=False)
    result = h.run("--uninstall")
    assert result.returncode == 0, result.stderr
    assert foreign.is_dir()
    assert "not installed from careerdocs-plugin" in result.stderr


def test_only_codex_never_touches_claude(tmp_path):
    h = Harness(tmp_path)
    result = h.run("--only", "codex")
    assert result.returncode == 0, result.stderr
    assert h.claude_calls() == []
    assert h.codex_cache().is_symlink()


def test_no_agent_detected_fails_with_guidance(tmp_path):
    h = Harness(tmp_path, claude=False, codex=False)
    result = h.run()
    assert result.returncode == 1
    assert "npx skills add bmcnaboe/careerdocs-plugin -g" in result.stdout


def test_bad_option_is_a_usage_error(tmp_path):
    result = Harness(tmp_path).run("--only", "cursor")
    assert result.returncode == 2
    assert "--only takes claude or codex" in result.stderr


def test_workspace_flag_records_creates_and_initializes(tmp_path):
    h = Harness(tmp_path)
    ws = tmp_path / "career"
    result = h.run("--workspace", str(ws))
    assert result.returncode == 0, result.stderr
    assert h.pointer().read_text(encoding="utf-8") == f"{ws}\n"
    assert json.loads((ws / "careerdocs.json").read_text(encoding="utf-8"))["version"] == "1"
    assert f"Workspace: {ws}" in result.stdout
    assert "careerdocs CLI runs" in result.stdout


def test_workspace_tilde_expands_to_home(tmp_path):
    h = Harness(tmp_path)
    result = h.run("--workspace", "~/career")
    assert result.returncode == 0, result.stderr
    assert h.pointer().read_text(encoding="utf-8").strip() == str(h.home / "career")
    assert (h.home / "career" / "careerdocs.json").is_file()


def test_claude_only_initializes_the_workspace_from_its_cache(tmp_path):
    h = Harness(tmp_path, codex=False)
    ws = tmp_path / "career"
    result = h.run("--workspace", str(ws))
    assert result.returncode == 0, result.stderr
    assert (ws / "careerdocs.json").is_file()
    assert "/careerdocs:onboard" in result.stdout and "$onboard" not in result.stdout


def test_codex_only_initializes_the_workspace_from_its_cache(tmp_path):
    h = Harness(tmp_path, claude=False)
    ws = tmp_path / "career"
    result = h.run("--workspace", str(ws))
    assert result.returncode == 0, result.stderr
    assert (ws / "careerdocs.json").is_file()
    assert "$onboard" in result.stdout


def test_dry_run_with_workspace_changes_nothing(tmp_path):
    h = Harness(tmp_path)
    ws = tmp_path / "career"
    result = h.run("--dry-run", "--workspace", str(ws))
    assert result.returncode == 0, result.stderr
    assert f"would create {ws}" in result.stdout
    assert not ws.exists() and not h.pointer().exists()


def test_uninstall_forgets_the_workspace_but_keeps_the_folder(tmp_path):
    h = Harness(tmp_path)
    ws = tmp_path / "career"
    assert h.run("--workspace", str(ws)).returncode == 0
    h.mark_installed()
    result = h.run("--uninstall")
    assert result.returncode == 0, result.stderr
    assert not h.pointer().exists()
    assert (ws / "careerdocs.json").is_file()
