<!--
SYNC IMPACT REPORT
==================
Version change: template → 1.0.0
Bump rationale: MAJOR — initial ratification.

Modified principles: none (initial set of six).
Added sections: Quality Gates; Development Workflow; Governance.
Removed sections: none.

Templates reviewed:
  ✅ .specify/templates/plan-template.md — Constitution Check gates map to the
     principles below; no structural change needed.
  ✅ .specify/templates/spec-template.md — no change needed.
  ✅ .specify/templates/overrides/tasks-template.md — project override written
     in the same change: gate tiers, [risky] surfaces, verification-evidence.
  ✅ .specify/templates/checklist-template.md — no change needed.

Follow-up TODOs: none.
-->

# career-documents Constitution

## Core Principles

### I. Applicant Data Never Enters the Repository (NON-NEGOTIABLE)

This repository is public. It MUST contain only workflow logic, schemas, tooling,
documentation, and sanitized examples. Qualifications, voice samples, personal
templates, generated documents, credentials, and every other piece of applicant data
live in applicant-owned locations outside the repository and outside any plugin
install directory. Examples and fixtures MUST use a fictional applicant with reserved
identifiers (`example.com` addresses, `555` telephone numbers, invented employers).
The gate MUST fail on personal-data patterns outside `examples/` and `tests/fixtures/`.

Rationale: a single leaked résumé fact is irreversible in public git history, so the
guard sits at the gate rather than in reviewer attention.

### II. Four Authorities, Modeled Separately

Qualifications, voice, document templates, and target role are four distinct
authorities. Each has its own schema, its own storage location, and its own owner. A
generated document is composed from all four; no authority may absorb another (voice
rules do not live in the profile, role requirements do not live in templates). The
optional `career-documents.json` only locates providers, templates, outputs, and
workflow policy; it MUST NOT store qualifications or credentials.

Rationale: separation is what lets one profile serve many roles, voices, and layouts
without duplication or drift.

### III. One Authoritative Profile, Changed Only by Approved Diffs

Exactly one configured provider is authoritative for qualifications at any time; every
other copy (exports, caches, generated documents) is derived and labeled as such.
Every fact carries a stable ID, provenance, verification state, dates, and
visibility. Every write to the authoritative profile is first shown to the applicant
as a reviewable diff and applied only on approval. Generated content MUST cite the
profile IDs it draws on; content with no citable source is a defect, never a fill-in.

Rationale: applicants must be able to trust that documents say only what they have
verified, and that there is one place to fix a fact.

### IV. Provider-Neutral Source, Thin Packages

Workflow logic lives once, in `skills/`, following the Agent Skills specification.
Platform packages (Claude Code/Cowork, ChatGPT/Codex) contain only manifests,
installers, and platform metadata. Runtime helpers are scripts the skills invoke, not
platform APIs. A behavioral difference between platforms is a bug.

Rationale: the ticket's portability promise is only kept if there is nothing to keep
in sync.

### V. Verified Output

A generated document is not done until it passes the deterministic checks: factual
traceability to profile IDs, link and date validity, text extraction, pagination
limits, and rendered-layout inspection. Every output records its source IDs, role
brief, template, voice profile, and plugin version. Checks run through scripts so the
same bar applies on every platform.

Rationale: the failure mode of generated career documents is quiet fabrication and
silent layout breakage; both are caught by checks, not by rereading.

### VI. Simplicity and Portability

Repository tooling is Python 3.11+ standard library. Runtime scripts declare their
dependencies inline (PEP 723) and run under `uv`, with the manual `pip` fallback
documented. The MVP uses existing file, MCP, and document tools; a hosted service,
custom UI, and application submission are out of scope. Prefer the smallest change
that satisfies the spec; complexity MUST be justified in the plan.

## Quality Gates

`scripts/gate.sh [basic|full|final]` owns the quality bar and is pinned in
`.ralph/command-policy`. `basic` runs unit tests and the skills lint; `full` adds
package and document checks; `final` adds shellcheck, the secrets scan, and the
agent-layer conformance check. Tasks tagged `[risky]` run the full gate before
commit; every other task runs basic. `final` MUST be green before a commit lands on
the default branch.

## Development Workflow

- Features are specified before they are built (Spec Kit: spec, plan, tasks); the
  active feature is named in `.specify/feature.json`.
- Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`),
  no co-author trailers or agent footers.
- Files synced from agent-layer are read-only here; edit them in agent-layer and
  `layer sync-project`.
- Work is tracked in Linear; a ticket moves to In Review when its work is committed
  and green, and to Done only after a human merges it.

## Governance

This constitution supersedes other practices in this repository. Amendments are made
by editing this file with a version bump (MAJOR for removed or redefined principles,
MINOR for new principles or materially expanded guidance, PATCH for clarifications),
a Sync Impact Report, and a review of the templates it governs. Every plan's
Constitution Check MUST cite these principles by number; every review verifies
compliance.

**Version**: 1.0.0 | **Ratified**: 2026-09-07 | **Last Amended**: 2026-09-07
