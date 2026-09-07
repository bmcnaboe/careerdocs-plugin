#!/usr/bin/env bash
# scripts/gate.sh — the quality bar, by tier.
#   basic : unit tests + skills lint
#   full  : basic + integration runs + inventory, version, and evidence checks
#   final : full + shellcheck + gitleaks + applicant-data guard + agent-layer conformance
# A component that does not exist yet is reported as SKIP so the bar can be built up
# task by task; --strict (or GATE_STRICT=1) turns every SKIP into a failure, which is
# the bar once setup has landed. `.ralph/command-policy` pins these three invocations.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 2

tier="basic"
strict="${GATE_STRICT:-0}"
for arg in "$@"; do
  case "$arg" in
    basic|full|final) tier="$arg" ;;
    --strict) strict=1 ;;
    *) echo "usage: scripts/gate.sh [basic|full|final] [--strict]" >&2; exit 2 ;;
  esac
done

fail=0
skips=0
run() {
  local label="$1"; shift
  echo "=== $label"
  if "$@"; then echo "ok: $label"; else echo "FAIL: $label"; fail=1; fi
}
skip() { echo "SKIP: $1"; skips=$((skips + 1)); }
have() { command -v "$1" >/dev/null 2>&1; }
pytest_suite() {
  local dir="$1"
  if [[ -f pyproject.toml && -d "$dir" ]]; then
    run "pytest $dir" uv run --extra dev python -m pytest -q "$dir"
  else
    skip "pytest $dir (pyproject.toml or $dir not present yet)"
  fi
}
py_check() {
  local script="$1"; local label="$2"
  if [[ -f "$script" ]]; then run "$label" python3 "$script"; else skip "$label ($script not present yet)"; fi
}

basic_tier() {
  pytest_suite tests/unit
  py_check scripts/lint_skills.py "skills lint"
}
full_tier() {
  basic_tier
  pytest_suite tests/integration
  py_check scripts/check_inventory.py "package inventory"
  py_check scripts/check_versions.py "version agreement"
  py_check scripts/verification_evidence_check.py "verification evidence"
}
final_tier() {
  full_tier
  if have shellcheck; then run "shellcheck" shellcheck scripts/*.sh; else skip "shellcheck (not installed)"; fi
  if have gitleaks; then run "gitleaks" gitleaks detect --no-banner --redact --source .; else skip "gitleaks (not installed)"; fi
  py_check scripts/pii_guard.py "applicant-data guard"
  run "agent-layer conformance" python3 scripts/agent-layer/check.py
}

case "$tier" in
  basic) basic_tier ;;
  full) full_tier ;;
  final) final_tier ;;
esac

if [[ "$strict" == 1 && "$skips" -gt 0 ]]; then
  echo "gate: $skips skipped component(s) under --strict"
  fail=1
fi
if [[ "$fail" -ne 0 ]]; then echo "gate: $tier RED"; exit 1; fi
echo "gate: $tier green"
