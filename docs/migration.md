# Migrating an existing career folder

A generic playbook for moving a folder that mixes résumés, exports, notes, and generated
documents into a `careerdocs` workspace. Run every command with
`--workspace <dir>`. Nothing about any specific applicant belongs in this repository — this
is the shape of the process, not anyone's data.

## 1. Inventory

```sh
careerdocs inventory <workspace>
```

Classifies every file — authoritative data, source evidence, template/voice input,
generated output, historical record, duplicate (by sha256), temporary, or unrelated — and
writes `inventory.json` and `inventory.md` with a recoverable destination per file. Review
`inventory.md` for sense (résumés are source evidence; copies under an `output/` folder are
duplicates or previous outputs; a scratch draft is temporary; non-career items under an
`archive/` folder are unrelated) and adjust destinations before organizing.

## 2. Configure

Write `careerdocs.json`. Keep `markdown` as the authoritative provider — the profile then
lives in `profile/` inside the workspace, versioned with everything else — and point it at
the templates, voice, outputs, and workflow-state locations. (Basic Memory as the
authority forces a derived Markdown mirror, and no flow uses its search.) Then:

```sh
careerdocs config validate
careerdocs doctor
```

`doctor` confirms the provider is reachable and reports template, voice, converter, and
dependency status.

## 3. Onboard

Register the sources and extract candidates, then propose, approve, and apply the profile:

```sh
careerdocs profile import <source>...
# The agent extracts candidates.json from the emitted text; the applicant statement of
# record is the highest-precedence source (provenance method "statement").
careerdocs profile diff candidates.json
careerdocs profile approve <diff_id>
careerdocs profile apply <diff_id>
```

Reconcile by precedence (an applicant statement beats an imported résumé); leave any
conflict that precedence cannot settle open, and confirm the facts that must survive are
present and `applicant_verified`.

## 4. Capture voice and templates

Draft `voice/voice.md` from the applicant's current documents and any brand or style
guidance. Convert the current résumé DOCX into `templates/resume/template.docx` plus a
`template.json` manifest — keep the styling, replace the content with the docxtpl
placeholders (`{{ contact_name }}`, `{{ contact_details }}`, and the `sections`/`units` loop), and set the page budget —
and derive a `templates/cover-letter/` template.

## 5. Generate and verify baselines

```sh
careerdocs plan  --baseline --positioning executive --kind resume
careerdocs render --baseline --positioning executive --kind resume --pdf
careerdocs check  baselines/executive/<file>.docx
# repeat for --positioning builder
```

Every baseline must pass the five checks (the PDF checks need LibreOffice; they are skipped
with a reason offline) before the previous current-state artifacts are archived.

## 6. Organize

```sh
careerdocs organize --inventory .careerdocs/inventory.json --apply
```

Moves each file under its reviewed destination (`sources/`, `templates/`, `voice/`,
`baselines/`, `applications/`, `archive/`), never deleting — duplicates, temporary files,
and unrelated items are relocated under `archive/`. Every move is recorded in
`.careerdocs/moves.jsonl`; `careerdocs organize --rollback` replays it. Write a
workspace `README.md` describing the resulting structure.
