---
name: careerdocs
description: Core conventions and the careerdocs CLI shared by the careerdocs flows (onboard, update, resume, cover letter). Consult this skill for how the four authorities (qualifications, voice, templates, target role) are modeled and located, how flow skills invoke the careerdocs CLI, the diff-then-approve rule for every profile change, visibility semantics, and where workflow state and generated outputs live. Load it before running any careerdocs command or when a flow skill references a convention it does not restate.
license: MIT
user-invocable: false
compatibility: "Python 3.11+; uv recommended (uv run), python3 fallback. Offline except optional link checks. Optional LibreOffice (soffice) for PDF conversion."
metadata:
  version: "0.1.0"
  author: "careerdocs-plugin contributors"
---

# careerdocs

Shared conventions and the `careerdocs` CLI behind four flows: **onboard**, **update**,
**resume**, **cover-letter**. The flow skills own the
conversation; this skill owns the rules they all obey and the deterministic commands they
all call. Read it before running any `careerdocs` command.

## The four authorities

Kept separate, never folded into one opaque profile:

1. **Qualifications** — the `CareerProfile`: entities (contact, experience, achievement,
   education, skill, project, credential, patent, publication) with stable IDs,
   provenance, verification state, visibility, and conflict records. Held by a
   **provider** — structured Markdown under `profile/` by default. A Basic Memory provider
   also exists, but no flow uses its search, and making it authoritative implies a derived
   Markdown mirror at `providers.markdown.path`.
2. **Voice** — how the applicant writes, in a `voice.md` with frontmatter (`voice.path`).
3. **Document templates** — a DOCX plus a sidecar `template.json` manifest, one per kind
   (`resume`, `cover_letter`), under `templates.dir`.
4. **Target role** — the `RoleBrief` for one application, under
   `outputs.applications_dir/<role-slug>/`.

An optional `careerdocs.json` only **locates** these; it stores no qualifications
and no credentials. Forbidden keys/values (credentials like `token`, `api_key`; or
qualification content like `entities`, `experience`) are refused by `config validate`.

## Invoking the CLI

Entry point: `skills/careerdocs/scripts/careerdocs.py`. Flow skills call it by
relative path:

```sh
uv run <skill-root>/careerdocs/scripts/careerdocs.py <command> --workspace <dir> [--json]
# python3 works too; the entry point declares its runtime deps inline (PEP 723).
```

- `--workspace <dir>` selects the applicant workspace (default: current directory).
- `--json` prints machine output on stdout; human output otherwise. Diagnostics go to
  stderr.
- Exit codes: **0** ok, **1** a check failed, **2** contract or usage error.

Commands (full contract in `references/`): `doctor`, `config init|validate`,
`profile validate|import|diff|approve|apply|export|status`, `brief`, `map`, `plan`,
`render`, `check`, `state show|answer|resume`, `version`.

The CLI is deterministic; the judgement steps happen **between** commands. A command
emits a JSON skeleton or candidate set, the agent fills it in, and the next command
validates and persists it. The agent never writes provider files directly.

## The diff-then-approve rule

Every change to the authoritative profile is a reviewable proposal, never a silent
write:

1. `profile diff <candidates.json>` → a `ProfileDiff` with a `base_hash` and a rendered
   Markdown summary. This never mutates the profile.
2. Show the rendered diff to the applicant and get an **explicit yes**.
3. `profile approve <diff_id>` → records a hash-bound approval (append-only).
4. `profile apply <diff_id>` → applies atomically, but only when the approval's hash
   matches the diff and the diff's `base_hash` still matches the current profile;
   otherwise it refuses. Apply refreshes derived exports and marks affected output
   records stale.

Never call `approve` without a real applicant yes. Never hand-edit provider files to
skip a diff.

## Visibility semantics

Every entity has `visibility` (`public` / `restricted` / `private`) and `verification`
(`unverified` / `imported` / `applicant_verified` / `externally_verified`).

- `private` entities are **never** rendered into a document and **never** appear in an
  export.
- `restricted` entities render only into a document that has a matching per-document
  approval (`profile approve --document <path>`).
- `unverified` facts never render.
- An **unresolved conflict** blocks the affected field from every document.

Renderers and exports call `visible_for(document)`; nothing bypasses it.

## Where state and outputs live

Relative to the workspace, under the configured directories (defaults shown):

- Authoritative profile: `profile/` (markdown provider) or the Basic Memory vault folder.
- Sources ledger: `sources.jsonl`; approvals: `approvals.jsonl`; diffs: `diffs/`.
- Application artifacts: `applications/<role-slug>/` — `brief.json`, `map.json`,
  `plan.json`.
- Rendered documents and their records: `outputs/` (`<file>.docx`, `.pdf`,
  `.record.json`).
- Generated baselines: `baselines/<positioning>/`.
- Workflow state: `.careerdocs/state/<flow>/<subject>.json` — append-only
  questions, the pending diff, and artifact paths, so any flow resumes without repeating
  a question.

## No applicant data in this repository

This is the plugin source. Real qualifications, voice samples, personal templates, and
generated documents live in the applicant's workspace, never here. Everything under
`examples/` is a sanitized fictional applicant. The applicant-data guard fails the build
on anything that looks like real personal data.

## References

- `references/schema.md` — the `CareerProfile` model and `careerdocs.json` schema.
- `references/provider-contract.md` — the provider interface and the two providers.
- `references/checks.md` — the five output checks.
- `references/configuration.md` — every config key and its default.
