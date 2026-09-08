# Onboard playbook

The onboarding flow, step by step. `careerdocs` is the CLI at
`skills/career-documents/scripts/careerdocs.py`; run every command with
`--workspace <dir>`.

## 1. Inventory the sources

Ask the applicant where their materials are: current and older resumes (DOCX/PDF), a
LinkedIn or network export (CSV), and any notes (Markdown/text). List them; you will pass
their paths to `profile import`.

## 2. Import

```sh
careerdocs profile import <path>... --workspace <dir> --json
```

This registers every source in the provider's `sources.jsonl` with a sha256, and returns,
per source: the `source_id`, the extracted `text_blocks`, and (for a network export) draft
`candidates`.

## 3. Extract candidates

Read the `text_blocks` and write `candidates.json`:

```json
{
  "candidates": [
    { "type": "contact", "ref": "contact", "provenance": { "source_id": "...", "method": "extraction", "recorded_at": "...", "actor": "agent", "excerpt": "..." }, "name": "..." },
    { "type": "experience", "ref": "role1", "provenance": { ... }, "organization": "...", "title": "...", "start_date": "YYYY-MM", "end_date": "YYYY-MM" },
    { "type": "achievement", "parent_ref": "role1", "provenance": { ... }, "statement": "..." }
  ]
}
```

Rules: type every candidate; give each a single `provenance` naming its `source_id` and an
`excerpt`; give experiences/skills/education a `ref`, and achievements a `parent_ref`
matching their parent's `ref`. **Never invent a fact** — if the sources do not state it, do
not write it. When two sources disagree on a field, include both candidates; the merge
records the disagreement as a conflict.

## 4. Diff

```sh
careerdocs profile diff candidates.json --flow onboard --subject <name> --workspace <dir> --json
```

Merges candidates by match key, applies precedence (applicant statement > verified import >
newest import), records disagreements as conflicts, and returns the `diff_id`, `base_hash`,
and the generated `questions`. The questions are persisted to workflow state.

## 5. Ask only the generated questions

For each question, ask the applicant in plain language and record the answer:

```sh
careerdocs state answer onboard <name> --question <id> --answer "<text>" --workspace <dir>
```

Do not ask anything the CLI did not generate. To see what remains:
`careerdocs state resume onboard <name>`.

## 6. Resolve and re-diff

Convert the answers to resolution operations (`resolve_conflict`, `update_field`,
`set_visibility`) and produce the final diff to review, so the proposed profile reflects
the applicant's choices.

## 7. Approve — only after an explicit yes

Show the rendered diff. Only when the applicant explicitly approves:

```sh
careerdocs profile approve <diff_id> --workspace <dir>
```

## 8. Apply

```sh
careerdocs profile apply <diff_id> --workspace <dir>
```

Writes the authoritative profile atomically and refreshes the derived export.

## 9. Export and confirm

```sh
careerdocs profile export --to <other-provider> --workspace <dir>   # if a derived copy is wanted
careerdocs profile validate --workspace <dir>
```

The result is one authoritative profile, with both provenance entries on any reconciled
role, and private facts absent from every export.
