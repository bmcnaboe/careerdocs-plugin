# Update playbook

Add or correct a qualification from an applicant statement. `<dir>` below is the
resolved workspace (`doctor` shows it); `--workspace <dir>` only overrides it.

## 1. Capture the statement with provenance

Record what the applicant said as a source with `method: statement` and
`actor: applicant`. An applicant statement is the highest-precedence source, so it beats a
conflicting prior import. Keep an `excerpt` of their words.

Build a `candidates.json` with the new fact — a new entity, or a field change on an
existing entity — each candidate carrying that statement provenance. For a correction to
an existing entity, target it by its match key (the merge dedups onto it and proposes an
`update_field`).

## 2. Diff

```sh
careerdocs profile diff candidates.json --flow update --subject <name> --workspace <dir> --json
```

Answer only any material questions the CLI generates (usually none for a clear statement),
recording answers with `careerdocs state answer update <name> --question <id> --answer …`.

## 3. Approve — only after an explicit yes

```sh
careerdocs profile approve <diff_id> --workspace <dir>
```

## 4. Apply

```sh
careerdocs profile apply <diff_id> --workspace <dir>
```

The new fact gets a fresh stable id, statement provenance, and `applicant_verified` state.
The authoritative profile and every derived export are refreshed together.

## 5. Report stale outputs

```sh
careerdocs profile status --workspace <dir>
```

Lists every previously generated résumé or letter whose cited facts changed. Tell the
applicant which documents to regenerate.

## Resuming

If interrupted before approval:

```sh
careerdocs state resume update <name> --workspace <dir>
```

shows the pending diff and any open question; continue from there without re-asking.
