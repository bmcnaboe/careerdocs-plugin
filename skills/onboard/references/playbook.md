# Onboard playbook

The onboarding flow, step by step. `careerdocs` is the CLI at
`skills/careerdocs/scripts/careerdocs.py`. `<dir>` below is the workspace: `doctor` shows
which folder resolved and how, and `--workspace <dir>` is only needed to override it.

## 0. Confirm the workspace

```sh
careerdocs doctor --json
```

If `workspace_source` is `cwd`, nothing marks that folder as a workspace and data commands
will refuse it. Ask the applicant which folder should hold their profile (the installer
suggests `~/career-workspace`) and record it:

```sh
careerdocs config workspace <dir>
```

In Cowork, skip the question: the folder attached to the session is the workspace. Run
`config init --workspace <that folder>` if it has no `careerdocs.json`, and pass
`--workspace <that folder>` on every command (the sandbox home does not persist, so a
recorded default is not available there).

## 1. Gather the materials

Ask the applicant where their materials are and list the paths; you will pass them to
`profile import`. In order of value:

| Material | Format | How to get it |
| --- | --- | --- |
| Résumés, current and older | DOCX, PDF | Already on disk; older versions carry roles the current one dropped |
| LinkedIn data export | CSV (`Positions.csv`, `Education.csv`, `Skills.csv`, `Certifications.csv`) | LinkedIn → Settings & Privacy → Data privacy → Get a copy of your data → tick the files (or the full archive) → download the zip from the email, usually within ten minutes → put the CSVs in `sources/` |
| Profile as PDF, the alternative to the export | PDF | On the applicant's own LinkedIn profile: More → Save to PDF; imports like a résumé |
| Notes and records | Markdown, text | Reviews, brag docs, project write-ups, a bio |
| Writing samples | any text | Cover letters, emails, posts the applicant likes; used for `voice.md`, not imported |

A profile URL is not an input: the page is behind a login and LinkedIn's terms forbid
fetching it. `Positions.csv` yields experience candidates with exact dates (the importer
reads `Company`/`Title`/`Started On`/`Finished On`); other CSVs are read as text blocks.

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
