---
name: update
description: Add a new qualification or correct an existing one in the applicant's authoritative profile from something they state, such as a new role, achievement, skill, credential, award, or a wrong date. The statement is recorded as a source, proposed as a diff, applied only after an explicit yes, and the documents it makes stale are reported. Resumable from a pending diff.
license: MIT
compatibility: "Python 3.10+; uv recommended. Requires the careerdocs core skill and an onboarded profile."
metadata:
  version: "0.6.0"
  author: "careerdocs-plugin contributors"
---

# update

Add or correct one fact the applicant states. Read the core `careerdocs` skill first;
commands and file shapes are in its `references/cli.md`.

1. **Record the statement as a source.** Write their words to
   `sources/statement-<date>-<topic>.md` and `profile import` it. An applicant statement
   outranks any earlier import.
2. **Write `candidates.json`**: a new entity, or the existing entity's match key with the
   changed field, each candidate citing that source with `method: statement` and
   `actor: applicant`.
3. `profile diff candidates.json --flow update --subject <topic>`; answer any question it
   generates with `state answer`.
4. **Show the summary.** After an explicit yes: `profile approve <diff_id>`, then
   `profile apply`. The new fact gets a fresh id and `applicant_verified` state.
5. `profile status` names the documents the change made stale; say which to regenerate.

Interrupted before approval: `state resume update <topic>` shows the pending diff.

## Guardrails

- Never hand-edit `profile/`; every change is a diff the applicant approves.
- Provenance is append-only; earlier sources stay recorded.
- Report staleness, never hide it.
