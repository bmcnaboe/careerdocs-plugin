#!/usr/bin/env bash
# install.sh — install the careerdocs plugin into Claude Code and Codex without cloning.
#
#   curl -fsSL https://raw.githubusercontent.com/bmcnaboe/careerdocs-plugin/main/install.sh | bash
#   curl -fsSL https://raw.githubusercontent.com/bmcnaboe/careerdocs-plugin/main/install.sh | bash -s -- --dry-run
#
# Every agent installs the plugin from this repository with its own plugin manager and
# keeps its own versioned copy; this script copies nothing itself. Idempotent, no sudo,
# and it writes only under ~/.claude, ~/.codex, ~/.config/careerdocs, and the workspace
# folder it asks you for. It reports Python 3.10+, uv (recommended), and LibreOffice
# (optional); asks which folder should be your workspace (the one folder that holds your
# profile, templates, voice, and generated documents) and records it so the skills find
# it from any session; then, for every agent it detects:
#   * Claude Code — adds the GitHub marketplace and installs (or updates) the plugin at
#     user scope;
#   * Codex — adds the same repository as a Git marketplace and installs (or refreshes)
#     the plugin, removing the skill copies that earlier versions of this script put
#     under ~/.agents/skills.
# Cowork keeps its own plugin list and has no command line, so the script ends with
# those steps, and with the steps for onboarding your materials.
#
# Options:
#   --only claude|codex   one agent instead of every agent detected
#   --workspace <dir>     the workspace folder (asked for interactively when omitted)
#   --ref <git-ref>       branch or tag to install from (default: main)
#   --dry-run             print what would happen without changing anything
#   --uninstall           remove what this script installed (the workspace stays)
#   -h, --help            this text
#
# Environment: CAREERDOCS_REPO (owner/repo) and CAREERDOCS_REF override where the plugin
# comes from.

set -euo pipefail

REPO="${CAREERDOCS_REPO:-bmcnaboe/careerdocs-plugin}"
REF="${CAREERDOCS_REF:-main}"
MARKETPLACE="careerdocs-plugin"   # the marketplace is named after the repository
PLUGIN="careerdocs"               # the plugin inside it; skills invoke as /careerdocs:<skill>
LEGACY_PLUGIN="careerdocs-plugin" # the plugin's name before it was shortened; replaced on upgrade
SKILLS=(careerdocs onboard update resume cover-letter)
LEGACY_SKILLS_DIR="${HOME}/.agents/skills"   # where earlier versions of this script copied the skills
CODEX_HOME_DIR="${CODEX_HOME:-${HOME}/.codex}"
CONFIG_DIR="${XDG_CONFIG_HOME:-${HOME}/.config}/careerdocs"
POINTER="${CONFIG_DIR}/workspace"   # one line: the recorded default workspace; the CLI reads it
DEFAULT_WORKSPACE="${HOME}/career-workspace"

only=""
workspace=""
dry_run=0
uninstall=0

usage() {
  cat <<'USAGE'
Usage: install.sh [--only claude|codex] [--workspace <dir>] [--ref <git-ref>] [--dry-run] [--uninstall]

Installs the careerdocs plugin into every agent it detects, each through its own plugin
manager: Claude Code (marketplace + plugin, user scope) and Codex (marketplace + plugin).
Records the workspace folder the skills work in, and prints the Cowork steps. Safe to
re-run.

  --only claude|codex   one agent instead of every agent detected
  --workspace <dir>     the workspace folder (asked for interactively when omitted)
  --ref <git-ref>       branch or tag to install from (default: main)
  --dry-run             print what would happen without changing anything
  --uninstall           remove what this script installed (the workspace stays)
  -h, --help            this text
USAGE
}

say()  { printf '%s\n' "$*"; }
ok()   { printf '  ok    %s\n' "$*"; }
note() { printf '  --    %s\n' "$*"; }
warn() { printf '  warn  %s\n' "$*" >&2; }
die()  { printf 'error: %s\n' "$*" >&2; exit 2; }
have() { command -v "$1" >/dev/null 2>&1; }
run() {
  if [ "$dry_run" = 1 ]; then printf '  would run: %s\n' "$*"; else "$@"; fi
}

while [ $# -gt 0 ]; do
  case "$1" in
    --only) shift; only="${1:-}" ;;
    --only=*) only="${1#--only=}" ;;
    --workspace) shift; workspace="${1:-}" ;;
    --workspace=*) workspace="${1#--workspace=}" ;;
    --ref) shift; REF="${1:-}" ;;
    --ref=*) REF="${1#--ref=}" ;;
    --dry-run) dry_run=1 ;;
    --uninstall) uninstall=1 ;;
    -h|--help) usage; exit 0 ;;
    *) die "unknown option: $1 (try --help)" ;;
  esac
  shift
done
case "$only" in ""|claude|codex) ;; *) die "--only takes claude or codex, not '$only'" ;; esac
[ -n "$REF" ] || die "--ref needs a value"

python_ok() {
  have python3 && python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null
}

preflight() {
  case "$(uname -s)" in
    MINGW*|MSYS*|CYGWIN*) die "Windows shells are not supported yet; use WSL, or follow docs/setup-claude.md and docs/setup-codex.md by hand" ;;
  esac
  say "Prerequisites"
  if python_ok; then
    ok "python3 $(python3 -c 'import platform; print(platform.python_version())')"
  elif have uv; then
    note "python3 3.10+ is not on PATH; uv will provision an interpreter for the careerdocs CLI"
  else
    die "Python 3.10+ or uv is required. Install uv: curl -LsSf https://astral.sh/uv/install.sh | sh"
  fi
  if have uv; then
    ok "uv $(uv --version 2>/dev/null | awk '{print $2}')"
  else
    warn "uv not found; the careerdocs CLI resolves its dependencies with uv. Install it: curl -LsSf https://astral.sh/uv/install.sh | sh"
  fi
  if have soffice; then
    ok "LibreOffice found; PDF output and the PDF checks are available"
  else
    note "LibreOffice not found; documents still render, and the PDF checks report as skipped"
  fi
}

# --- Claude Code -----------------------------------------------------------------------

claude_marketplace_present() { claude plugin marketplace list --json 2>/dev/null | grep -q "\"${MARKETPLACE}\""; }
claude_plugin_present() { claude plugin list --json 2>/dev/null | grep -q "\"${PLUGIN}@${MARKETPLACE}\""; }
claude_legacy_present() { claude plugin list --json 2>/dev/null | grep -q "\"${LEGACY_PLUGIN}@${MARKETPLACE}\""; }

install_claude() {
  say "Claude Code"
  local source="${REPO}"
  [ "$REF" = "main" ] || source="https://github.com/${REPO}.git#${REF}"
  if claude_marketplace_present; then
    run claude plugin marketplace update "${MARKETPLACE}"
    ok "refreshed marketplace ${MARKETPLACE}"
  else
    run claude plugin marketplace add "${source}"
    ok "added marketplace ${source}"
  fi
  if claude_legacy_present; then
    run claude plugin uninstall "${LEGACY_PLUGIN}@${MARKETPLACE}" --scope user
    ok "removed the install made under the plugin's old name, ${LEGACY_PLUGIN}"
  fi
  if claude_plugin_present; then
    run claude plugin update "${PLUGIN}@${MARKETPLACE}"
    ok "updated ${PLUGIN}"
  else
    run claude plugin install "${PLUGIN}@${MARKETPLACE}" --scope user
    ok "installed ${PLUGIN} at user scope"
  fi
  note "new Claude Code sessions load it; in a session that is already open, run /reload-plugins"
}

uninstall_claude() {
  say "Claude Code"
  if claude_plugin_present; then
    run claude plugin uninstall "${PLUGIN}@${MARKETPLACE}" --scope user
    ok "uninstalled ${PLUGIN}"
  elif claude_legacy_present; then
    run claude plugin uninstall "${LEGACY_PLUGIN}@${MARKETPLACE}" --scope user
    ok "uninstalled ${LEGACY_PLUGIN}"
  else
    note "plugin not installed"
  fi
  if claude_marketplace_present; then
    run claude plugin marketplace remove "${MARKETPLACE}"
    ok "removed marketplace ${MARKETPLACE}"
  else
    note "marketplace not configured"
  fi
}

# --- Codex -----------------------------------------------------------------------------

codex_has_plugins() { codex plugin --help >/dev/null 2>&1; }
codex_marketplace_present() { codex plugin marketplace list 2>/dev/null | grep -q "^${MARKETPLACE}[[:space:]]"; }
codex_plugin_present() { codex plugin list 2>/dev/null | grep -q "^${PLUGIN}@${MARKETPLACE}[[:space:]]*installed"; }

# Earlier versions of this script copied the skills into ~/.agents/skills. Those copies
# would shadow the plugin's skills and drift from it, so they go; a folder of the same
# name that did not come from this plugin is left alone.
remove_legacy_codex_copies() {
  local skill dir removed=0
  for skill in "${SKILLS[@]}"; do
    dir="${LEGACY_SKILLS_DIR}/${skill}"
    if [ -L "$dir" ] || [ -e "$dir" ]; then
      if [ -L "$dir" ] || grep -qs "careerdocs-plugin contributors" "$dir/SKILL.md"; then
        run rm -rf "$dir"
        removed=$((removed + 1))
      else
        warn "left ${dir} alone: it was not installed from careerdocs-plugin"
      fi
    fi
  done
  [ "$removed" = 0 ] || ok "removed ${removed} skill folder(s) an earlier version of this script copied into ${LEGACY_SKILLS_DIR}"
}

install_codex() {
  say "Codex"
  if ! codex_has_plugins; then
    warn "this Codex ($(codex --version 2>/dev/null | head -n 1)) has no plugin commands; update Codex and re-run, or see docs/setup-codex.md"
    return 0
  fi
  local source="${REPO}"
  [ "$REF" = "main" ] || source="${REPO}@${REF}"
  if codex_marketplace_present; then
    if run codex plugin marketplace upgrade "${MARKETPLACE}"; then
      ok "refreshed marketplace ${MARKETPLACE}"
    else
      note "marketplace ${MARKETPLACE} is not a Git marketplace here; left as it is"
    fi
  else
    run codex plugin marketplace add "${source}"
    ok "added marketplace ${source}"
  fi
  local had=0
  codex_plugin_present && had=1
  run codex plugin add "${PLUGIN}@${MARKETPLACE}"
  if [ "$had" = 1 ]; then ok "updated ${PLUGIN}"; else ok "installed ${PLUGIN}"; fi
  remove_legacy_codex_copies
  note "new Codex sessions load it; restart a session that is already open"
}

uninstall_codex() {
  say "Codex"
  if codex_has_plugins; then
    if codex_plugin_present; then
      run codex plugin remove "${PLUGIN}@${MARKETPLACE}"
      ok "uninstalled ${PLUGIN}"
    else
      note "plugin not installed"
    fi
    if codex_marketplace_present; then
      run codex plugin marketplace remove "${MARKETPLACE}"
      ok "removed marketplace ${MARKETPLACE}"
    else
      note "marketplace not configured"
    fi
  fi
  remove_legacy_codex_copies
}

# --- The installed CLI -----------------------------------------------------------------

# The careerdocs CLI entry point inside an installed copy: the newest version in the
# Claude Code or Codex plugin cache. Fails when neither agent has installed the plugin.
careerdocs_entry() {
  local cache entry newest=""
  for cache in "${HOME}/.claude/plugins/cache" "${CODEX_HOME_DIR}/plugins/cache"; do
    for entry in "${cache}/${MARKETPLACE}/${PLUGIN}"/*/skills/careerdocs/scripts/careerdocs.py; do
      [ -f "$entry" ] || continue
      if [ -z "$newest" ] || [ "$entry" -nt "$newest" ]; then newest="$entry"; fi
    done
  done
  [ -n "$newest" ] || return 1
  printf '%s\n' "$newest"
}

# Runs the CLI with whatever can run it (uv resolves its inline dependencies; python3
# installs them on first run). Fails quietly when nothing can, so callers treat it as
# best-effort.
careerdocs_cli() {
  local entry
  entry="$(careerdocs_entry)" || return 1
  if have uv; then uv run "$entry" "$@"
  elif python_ok; then python3 "$entry" "$@"
  else return 1
  fi
}

smoke_test() {
  local entry version
  if ! entry="$(careerdocs_entry)"; then
    note "skipped the CLI check: no installed copy of the plugin was found"
    return 0
  fi
  if have uv; then note "checking the careerdocs CLI (the first run resolves its dependencies)"; fi
  if version="$(careerdocs_cli version 2>/dev/null | head -n 1)" && [ -n "$version" ]; then
    ok "careerdocs CLI runs (${version})"
  elif have uv || python_ok; then
    warn "the careerdocs CLI did not run cleanly; try: uv run ${entry} version"
  else
    note "skipped the CLI check; it needs uv, or python3 with the CLI's dependencies installed"
  fi
}

# --- Workspace -------------------------------------------------------------------------

# Chooses the workspace: --workspace, else a prompt on the terminal (default: the folder
# recorded by an earlier run, else ~/career-workspace). Not a terminal: leave it unset.
ask_workspace() {
  say "Workspace"
  local default="$DEFAULT_WORKSPACE" recorded=""
  if [ -s "$POINTER" ]; then
    recorded="$(head -n 1 "$POINTER")"
    [ -d "$recorded" ] && default="$recorded"
  fi
  if [ -z "$workspace" ]; then
    if [ "$dry_run" = 1 ]; then
      note "would ask for the workspace folder (default ${default}) and record it in ${POINTER}"
      return 0
    fi
    if [ -t 1 ] && [ -r /dev/tty ]; then
      say "  careerdocs keeps your profile, templates, voice, and generated documents in one"
      say "  folder, your workspace. Nothing in it is sent anywhere."
      printf '  Workspace folder [%s]: ' "$default"
      read -r workspace < /dev/tty || workspace=""
      [ -n "$workspace" ] || workspace="$default"
    else
      note "not running in a terminal, so no workspace folder was chosen; re-run with"
      note "--workspace <dir>, or in an agent session run: careerdocs config workspace <dir>"
      return 0
    fi
  fi
  workspace="${workspace/#\~/$HOME}"
  case "$workspace" in /*) ;; *) workspace="${PWD}/${workspace}" ;; esac
}

# Creates the chosen workspace, records it, and writes its careerdocs.json (best-effort:
# the CLI may not be runnable yet; the agent writes the file on first use if so).
setup_workspace() {
  [ -n "$workspace" ] || return 0
  if [ "$dry_run" = 1 ]; then
    note "would create ${workspace}, record it in ${POINTER}, and write ${workspace}/careerdocs.json"
    return 0
  fi
  mkdir -p "$workspace" "$CONFIG_DIR"
  printf '%s\n' "$workspace" > "$POINTER"
  ok "workspace ${workspace} recorded in ${POINTER}"
  if careerdocs_cli config init --workspace "$workspace" >/dev/null 2>&1; then
    ok "${workspace}/careerdocs.json is in place"
  else
    note "could not run the careerdocs CLI here; the agent writes careerdocs.json on first use"
  fi
}

forget_workspace() {
  if [ -f "$POINTER" ]; then
    run rm -f "$POINTER"
    rmdir "$CONFIG_DIR" 2>/dev/null || true
    ok "forgot the recorded workspace (${POINTER}); the workspace folder itself is untouched"
  fi
}

# --- What comes next -------------------------------------------------------------------

# What comes next: Cowork's own install, then the onboard skill, which is the guided
# setup and tutorial. The steps live there, not here.
guidance() {
  local claude="$1" codex="$2"
  say ""
  say "Done."
  if [ -n "$workspace" ]; then
    say "Workspace: ${workspace}"
  else
    say "Workspace: none recorded yet (see above)."
  fi
  say ""
  say "Cowork keeps its own plugin list, so it takes three clicks in the desktop app:"
  say "  Cowork tab > Customize > Plugins > Add marketplace > ${REPO}, then install careerdocs."
  say ""
  say "Next, open a NEW session and run the onboard skill. It checks what is already set up,"
  say "walks you through gathering your materials, builds your profile, and shows you how the"
  say "plugin works from there:"
  [ "$claude" = 1 ] && say "  Claude Code:  /careerdocs:onboard"
  [ "$codex" = 1 ]  && say "  Codex:        \$onboard"
  say "  Cowork:       /careerdocs:onboard, with the workspace folder attached to the session"
}

main() {
  local want_claude=0 want_codex=0
  if [ "$only" != "codex" ] && have claude; then want_claude=1; fi
  if [ "$only" != "claude" ] && have codex; then want_codex=1; fi
  if [ "$only" = "claude" ] && [ "$want_claude" = 0 ]; then die "Claude Code (claude) is not on PATH"; fi
  if [ "$only" = "codex" ] && [ "$want_codex" = 0 ]; then die "Codex (codex) is not on PATH"; fi
  if [ "$want_claude" = 0 ] && [ "$want_codex" = 0 ]; then
    say "Neither Claude Code (claude) nor Codex (codex) is on PATH."
    say "Install one of them and re-run. Cowork needs no install here (see docs/setup-claude.md);"
    say "other agents: npx skills add ${REPO} -g"
    exit 1
  fi

  if [ "$uninstall" = 1 ]; then
    [ "$want_claude" = 1 ] && uninstall_claude
    [ "$want_codex" = 1 ] && uninstall_codex
    forget_workspace
    say "Removed."
    return 0
  fi

  preflight
  ask_workspace
  [ "$want_claude" = 1 ] && install_claude
  [ "$want_codex" = 1 ] && install_codex
  setup_workspace
  if [ "$dry_run" = 1 ]; then
    say "Dry run: nothing was changed."
    return 0
  fi
  smoke_test
  guidance "$want_claude" "$want_codex"
}

main
