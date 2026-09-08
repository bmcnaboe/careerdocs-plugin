#!/usr/bin/env bash
# install.sh — install careerdocs-plugin into Claude Code and Codex without cloning.
#
#   curl -fsSL https://raw.githubusercontent.com/bmcnaboe/careerdocs-plugin/main/install.sh | bash
#   curl -fsSL https://raw.githubusercontent.com/bmcnaboe/careerdocs-plugin/main/install.sh | bash -s -- --dry-run
#
# Idempotent, no sudo, and it writes only under ~/.claude, ~/.agents, and a temporary
# directory. It reports Python 3.11+, uv (recommended), and LibreOffice (optional); then,
# for every agent it detects:
#   * Claude Code — adds the GitHub marketplace and installs (or updates) the plugin at
#     user scope;
#   * Codex — downloads the repository archive and copies the skills into ~/.agents/skills
#     with the repository's own installer (packages/openai/install.py --copy).
#
# Options:
#   --only claude|codex   one agent instead of every agent detected
#   --ref <git-ref>       branch or tag to install from (default: main)
#   --dry-run             print what would happen without changing anything
#   --uninstall           remove what this script installed
#   -h, --help            this text
#
# Environment: CAREERDOCS_REPO (owner/repo), CAREERDOCS_REF, and CAREERDOCS_ARCHIVE_URL
# override where the plugin comes from; the tests point the last one at a local file.

set -euo pipefail

REPO="${CAREERDOCS_REPO:-bmcnaboe/careerdocs-plugin}"
REF="${CAREERDOCS_REF:-main}"
PLUGIN="careerdocs-plugin" # the plugin and its marketplace share this name
SKILLS=(careerdocs career-onboard career-update career-resume career-cover-letter)
SKILLS_DIR="${HOME}/.agents/skills"

only=""
dry_run=0
uninstall=0
TMP=""
trap 'if [ -n "$TMP" ]; then rm -rf "$TMP"; fi' EXIT

usage() {
  cat <<'USAGE'
Usage: install.sh [--only claude|codex] [--ref <git-ref>] [--dry-run] [--uninstall]

Installs careerdocs-plugin into every agent it detects: Claude Code (marketplace +
plugin, user scope) and Codex (skills copied into ~/.agents/skills). Safe to re-run.

  --only claude|codex   one agent instead of every agent detected
  --ref <git-ref>       branch or tag to install from (default: main)
  --dry-run             print what would happen without changing anything
  --uninstall           remove what this script installed
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
  have python3 && python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null
}
# Runs a Python script with the interpreter available: python3 when it is 3.11+, else a
# uv-provisioned one (uv downloads an interpreter when none is installed).
py() {
  if python_ok; then python3 "$@"; else uv run --no-project --python 3.12 python "$@"; fi
}

preflight() {
  case "$(uname -s)" in
    MINGW*|MSYS*|CYGWIN*) die "Windows shells are not supported yet; use WSL, or follow docs/setup-claude.md and docs/setup-codex.md by hand" ;;
  esac
  say "Prerequisites"
  if python_ok; then
    ok "python3 $(python3 -c 'import platform; print(platform.python_version())')"
  elif have uv; then
    note "python3 3.11+ is not on PATH; uv will provision an interpreter for the careerdocs CLI"
  else
    die "Python 3.11+ or uv is required. Install uv: curl -LsSf https://astral.sh/uv/install.sh | sh"
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

claude_marketplace_present() { claude plugin marketplace list --json 2>/dev/null | grep -q "\"${PLUGIN}\""; }
claude_plugin_present() { claude plugin list --json 2>/dev/null | grep -qE "\"${PLUGIN}(@${PLUGIN})?\""; }

install_claude() {
  say "Claude Code"
  local source="${REPO}"
  [ "$REF" = "main" ] || source="https://github.com/${REPO}.git#${REF}"
  if claude_marketplace_present; then
    ok "marketplace ${PLUGIN} already added"
  else
    run claude plugin marketplace add "${source}"
    ok "added marketplace ${source}"
  fi
  if claude_plugin_present; then
    run claude plugin update "${PLUGIN}@${PLUGIN}"
    ok "updated ${PLUGIN}"
  else
    run claude plugin install "${PLUGIN}@${PLUGIN}" --scope user
    ok "installed ${PLUGIN} at user scope"
  fi
  note "new Claude Code sessions load it; in a session that is already open, run /reload-plugins"
}

uninstall_claude() {
  say "Claude Code"
  if claude_plugin_present; then
    run claude plugin uninstall "${PLUGIN}@${PLUGIN}" --scope user
    ok "uninstalled ${PLUGIN}"
  else
    note "plugin not installed"
  fi
  if claude_marketplace_present; then
    run claude plugin marketplace remove "${PLUGIN}"
    ok "removed marketplace ${PLUGIN}"
  else
    note "marketplace not configured"
  fi
}

install_codex() {
  say "Codex"
  local url="${CAREERDOCS_ARCHIVE_URL:-https://github.com/${REPO}/archive/${REF}.tar.gz}"
  if [ "$dry_run" = 1 ]; then
    note "would download ${url} and copy these skills into ${SKILLS_DIR}: ${SKILLS[*]}"
    return 0
  fi
  TMP="$(mktemp -d)"
  curl -fsSL "$url" -o "$TMP/archive.tar.gz" || die "could not download ${url}"
  mkdir -p "$TMP/src"
  tar -xzf "$TMP/archive.tar.gz" -C "$TMP/src" --strip-components=1
  py "$TMP/src/packages/openai/install.py" --copy --home "$HOME" | sed 's/^/        /'
  ok "skills copied into ${SKILLS_DIR}"
}

uninstall_codex() {
  say "Codex"
  local skill dir removed=0
  for skill in "${SKILLS[@]}"; do
    dir="${SKILLS_DIR}/${skill}"
    if [ -L "$dir" ] || [ -e "$dir" ]; then
      if [ -L "$dir" ] || grep -qs "careerdocs-plugin contributors" "$dir/SKILL.md"; then
        run rm -rf "$dir"
        removed=$((removed + 1))
      else
        warn "left ${dir} alone: it was not installed from careerdocs-plugin"
      fi
    fi
  done
  ok "removed ${removed} skill(s) from ${SKILLS_DIR}"
}

smoke_test() {
  local entry="${SKILLS_DIR}/careerdocs/scripts/careerdocs.py" version
  [ -f "$entry" ] || return 0
  if have uv; then
    note "checking the careerdocs CLI (the first run resolves its dependencies)"
    if version="$(uv run "$entry" version 2>/dev/null | head -n 1)"; then
      ok "careerdocs CLI runs (${version})"
    else
      warn "the careerdocs CLI did not run cleanly; try: uv run ${entry} version"
    fi
  elif python_ok && version="$(python3 "$entry" version 2>/dev/null | head -n 1)"; then
    ok "careerdocs CLI runs (${version})"
  else
    note "skipped the CLI check; it needs uv, or python3 with the CLI's dependencies installed"
  fi
}

main() {
  local want_claude=0 want_codex=0
  if [ "$only" != "codex" ] && have claude; then want_claude=1; fi
  if [ "$only" != "claude" ] && { have codex || [ -d "${HOME}/.codex" ]; }; then want_codex=1; fi
  if [ "$only" = "claude" ] && [ "$want_claude" = 0 ]; then die "Claude Code (claude) is not on PATH"; fi
  if [ "$only" = "codex" ] && [ "$want_codex" = 0 ]; then die "Codex was not found (no codex on PATH and no ~/.codex)"; fi
  if [ "$want_claude" = 0 ] && [ "$want_codex" = 0 ]; then
    say "Neither Claude Code (claude) nor Codex (codex, ~/.codex) was found."
    say "Install one of them and re-run, or for other agents: npx skills add ${REPO} -g"
    exit 1
  fi

  if [ "$uninstall" = 1 ]; then
    [ "$want_claude" = 1 ] && uninstall_claude
    [ "$want_codex" = 1 ] && uninstall_codex
    say "Removed."
    return 0
  fi

  preflight
  [ "$want_claude" = 1 ] && install_claude
  [ "$want_codex" = 1 ] && install_codex
  if [ "$dry_run" = 1 ]; then
    say "Dry run: nothing was changed."
    return 0
  fi
  [ "$want_codex" = 1 ] && smoke_test
  say ""
  say "Done. Open your agent in the folder that holds your résumés and say:"
  say '  "onboard my career documents"'
}

main
