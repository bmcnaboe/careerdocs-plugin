# AGENTS.md

Working conventions for coding agents in this repo. `CLAUDE.md` is a pure pointer to
this file, so Claude Code and Codex read the same conventions.

## What this is

careerdocs-plugin is a portable, open-source resume and cover-letter plugin for AI
coding agents: one provider-neutral workflow source, packaged thinly for
ChatGPT/Codex and Claude Code/Cowork. It works without agent-layer; agent-layer may
install it.

## Hard rules

- **No applicant data, ever.** Qualifications, voice samples, personal templates,
  credentials, and generated documents stay outside this repository. Everything
  under examples and templates here is sanitized and fictional.
- **Four authorities stay separate**: qualifications, voice, document templates, and
  target role. Nothing folds them into one opaque profile.
- **Authoritative updates are proposals.** A change to an applicant's profile is a
  reviewable diff the applicant approves, never a silent write.
- **Provider-neutral first.** Workflow logic lives once in the shared source; the
  platform packages adapt packaging and invocation only.
- **Synced agent-layer files are read-only here** (`.claude/skills/linear-*`,
  `.claude/skills/speckit-*`, `.claude/hooks/*`, `scripts/agent-layer/check.py`,
  `.github/workflows/agent-layer.yml`, `scripts/dev/ralph/*`): edit them in
  agent-layer, then `layer sync-project`. Seeded files (`.claude/linear-workspace.md`,
  `CLAUDE.md`) are project-owned.

## Runs

Work is planned as Linear runs: `linear-specs/<stamp>-<slug>/plan.md` is the run plan
the Ralph loop executes (tasks, tranches, ticket snapshots), and `design/` beside it
holds the design of record (spec, implementation plan, research, data model,
contracts, quickstart, verification evidence). Spec Kit stays available for a future
spec-first feature; it expects its current-plan pointer in `CLAUDE.md`, which is a pure
pointer here, so the markers live in this imported file instead.

<!-- SPECKIT START -->
No active Spec Kit feature. Current run: `linear-specs/20260907-185131-agl-15-16-career-documents/plan.md`.
<!-- SPECKIT END -->

## Commands

```sh
./scripts/gate.sh [basic|full|final] [--strict]   # quality gate; basic is the default
```

`basic` runs the unit tests and skills lint; `full` adds the integration runs and the
inventory, version, and evidence checks; `final` adds shellcheck, gitleaks, the
applicant-data guard, and the agent-layer conformance check. A component that does not
exist yet reports `SKIP`; `--strict` makes that a failure. `final --strict` must be green
before a commit lands on `main`. `.ralph/command-policy` pins the three tiers for
autonomous runs.

## Tickets

Work is tracked in the `agent-layer` Linear workspace, team `agent-layer` (`AGL-`),
project `job-applier`. `.claude/linear-workspace.md` pins the workspace, states, and
house rules the `linear-*` skills read; it is seeded, project-owned, and safe to edit.
