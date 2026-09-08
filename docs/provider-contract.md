# Provider contract

A provider stores the authoritative `CareerProfile` or a derived copy. Exactly one
provider is authoritative, chosen by `providers.authoritative` in the config. The
structured-Markdown provider is the reference implementation; the Basic Memory provider
writes the same entities as vault notes. The `careerdocs profile` subcommands drive both.

## Interface

| Operation | Rules |
| --- | --- |
| `read()` | Returns the profile, validated against the schema and rules; refuses a `schema_version` newer than the CLI supports (`SCHEMA_TOO_NEW`). |
| `hash()` | SHA-256 over the canonical JSON of the sorted entities plus the index — stable regardless of file order. |
| `write(profile)` | Persists atomically; the only writer. |
| `export(target)` | Produces a derived copy; drops `private`, labels it `derived: true`; a derived copy is never applied back. |
| `capabilities()` | `{ authoritative_ok, search, context }`. Basic Memory reports `search` and `context`; Markdown reports neither. |
| source / approval / diff ledgers | `sources.jsonl`, append-only `approvals.jsonl`, `diffs/<diff_id>.json`. |

The diff → approve → apply orchestration lives in the CLI over these primitives:

1. `profile diff` builds a `ProfileDiff` with a `base_hash`, never mutating the profile.
2. `profile approve` records a hash-bound approval (append-only) after an explicit yes.
3. `profile apply` refuses unless the approval's hash matches the diff and the diff's
   `base_hash` still matches the current profile (`APPROVAL_MISSING`, `BASE_HASH_MISMATCH`);
   it applies atomically, refreshes the derived export, and marks stale outputs.

## Structured Markdown (reference)

- Location: `providers.markdown.path` (default `profile/`).
- Layout: `profile.md` index; `<type>/<id>.md` per entity (frontmatter = the entity's
  fields, body = the statement or summary); `sources.jsonl`; `approvals.jsonl`; `diffs/`.
- Frontmatter is JSON (a valid YAML subset) so nested fields round-trip without a YAML
  dependency.

## Basic Memory (first MCP provider)

- Location: `providers.basic_memory.vault_path` + `folder` (default `career/`), within the
  named project.
- Layout: the same per-entity files as Basic Memory notes — frontmatter with `title`,
  `type`, `permalink` (`<folder>/<type>/<id>`), `tags`, and every schema field; body with
  `## Statement`, `## Observations`, and `## Relations`.
- Writes are plain file writes; Basic Memory's watcher indexes them. The MCP tools are for
  retrieval only and are never the sole write path.
- `export(markdown)` produces the structured-Markdown layout with `derived: true`.
- No flow calls `search` or `context`; they exist for retrieval from other sessions.
  Making Basic Memory authoritative implies a derived Markdown mirror at
  `providers.markdown.path`, refreshed on every `apply`.

## Errors

Typed, with machine codes: `SCHEMA_TOO_NEW`, `PROFILE_INVALID`, `NOT_AUTHORITATIVE`,
`APPROVAL_MISSING`, `BASE_HASH_MISMATCH`, `PROVIDER_UNREACHABLE`. CLI exit codes: 0 ok,
1 a check failed, 2 a contract or usage error.
