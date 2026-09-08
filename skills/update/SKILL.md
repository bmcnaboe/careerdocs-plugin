---
name: update
description: Update the authoritative profile with a new qualification the applicant states. Use when the applicant reports a new achievement, role, skill, credential, or a correction, and it should become part of their one authoritative profile. The flow captures the statement with provenance (the applicant's own statement is the highest-precedence source), turns it into candidates, proposes a ProfileDiff, gets an explicit approval, applies it (giving the new fact a fresh stable id and applicant-verified state), refreshes the derived export, and reports which previously generated documents are now stale. Resumable — an interrupted update resumes from its pending diff without re-asking.
license: MIT
compatibility: "Python 3.11+; uv recommended. Requires the careerdocs core skill and an onboarded profile."
metadata:
  version: "0.1.0"
  author: "careerdocs-plugin contributors"
---

# update

Add or correct a qualification the applicant states, keeping one authoritative profile.
Read the core `careerdocs` skill first.

## When to use

The applicant reports something new or a correction — "I shipped X", "I now lead Y", "my
end date at Z was actually June" — and wants it in the profile. This is the day-to-day
maintenance flow after onboarding.

## The flow

Full detail in `references/playbook.md`.

1. **Capture the statement with provenance** — record the applicant's statement as a
   source (`method: statement`, `actor: applicant`). An applicant statement is the
   highest-precedence source, so it wins over prior imports.
2. **Build candidates** — turn the statement into typed candidates (a new entity, or a
   field update to an existing one), each carrying the statement provenance.
3. **`profile diff candidates.json --flow update --subject <name>`** — propose the change;
   answer only any material questions the CLI generates.
4. **`profile approve <diff_id>`** — only after an explicit applicant yes.
5. **`profile apply <diff_id>`** — the new fact gets a fresh stable id and
   `applicant_verified` state; the authoritative profile and every derived export agree.
6. **`profile status`** — report which earlier outputs are now stale (their cited facts
   changed) so the applicant can regenerate them.

## Resuming

If interrupted before approval, `state resume update <subject>` shows the pending diff;
continue from it without re-asking. `profile status` also surfaces a pending derived-export
refresh.

## Guardrails

- Authoritative updates are proposals: never hand-edit the profile; always diff → approve
  → apply.
- Provenance is append-only: the new statement provenance is added, prior provenance is
  kept.
- Report, don't hide, staleness: name the outputs a change invalidates.
