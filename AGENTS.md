# AGENTS.md

Working conventions for coding agents in this repo. `CLAUDE.md` is a pure pointer to
this file, so Claude Code and Codex read the same conventions.

## What this is

career-documents is a portable, open-source resume and cover-letter plugin for AI
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

## Spec Kit

Features are specified before they are built: `specs/<stamp>-<name>/` holds the
spec, plan, and tasks, and `.specify/feature.json` names the active feature. Spec Kit
expects its current-plan pointer in `CLAUDE.md`; that file is a pure pointer here, so
the markers live in this imported file instead.

<!-- SPECKIT START -->
No active plan yet.
<!-- SPECKIT END -->

## Commands

None yet. The first feature's plan defines the quality gate, and
`.ralph/command-policy` pins it for autonomous runs.

## Tickets

Work is tracked in the `agent-layer` Linear workspace, team `agent-layer` (`AGL-`),
project `job-applier`. `.claude/linear-workspace.md` pins the workspace, states, and
house rules the `linear-*` skills read; it is seeded, project-owned, and safe to edit.
