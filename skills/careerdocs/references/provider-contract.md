# Provider contract reference

A provider stores the authoritative `CareerProfile` or a derived copy. Exactly one is
authoritative (`providers.authoritative`). Structured Markdown is the reference provider;
Basic Memory writes the same entities as vault notes. The `careerdocs profile` subcommands
drive both.

## Interface

- `read()` — validated profile; refuses a newer `schema_version` (`SCHEMA_TOO_NEW`).
- `hash()` — SHA-256 over the canonical JSON of the sorted entities plus the index; stable
  regardless of file order.
- `write(profile)` — the only writer; atomic.
- `export(target)` — a derived copy; drops `private`, labels it `derived: true`; never
  applied back.
- `capabilities()` — `{ authoritative_ok, search, context }` (Basic Memory has search and
  context; Markdown has neither).
- ledgers — `sources.jsonl`, append-only `approvals.jsonl`, `diffs/<diff_id>.json`.

The diff → approve → apply flow lives over these primitives: `profile diff` builds a diff
with a `base_hash` (no mutation); `profile approve` records a hash-bound approval after an
explicit yes; `profile apply` refuses unless the approval hash matches and the diff's
`base_hash` still matches (`APPROVAL_MISSING`, `BASE_HASH_MISMATCH`), then applies
atomically, refreshes the derived export, and marks stale outputs.

## Structured Markdown

Location `providers.markdown.path` (default `profile/`). Layout: `profile.md` index;
`<type>/<id>.md` per entity (frontmatter = fields as JSON, body = statement/summary);
`sources.jsonl`; `approvals.jsonl`; `diffs/`.

## Basic Memory

Location `vault_path` + `folder` (default `career/`) in the named project. Each entity is a
note: frontmatter `title`, `type`, `permalink` (`<folder>/<type>/<id>`), `tags`, and every
field; body `## Statement`, `## Observations`, `## Relations`. Writes are plain file writes
the watcher indexes; the MCP tools are for retrieval only. `export(markdown)` yields the
Markdown layout with `derived: true`. No flow calls `search` or `context`; they exist for
retrieval from other sessions. Authoritative Basic Memory implies a derived Markdown
mirror at `providers.markdown.path`, refreshed on every `apply`.

## Errors

`SCHEMA_TOO_NEW`, `PROFILE_INVALID`, `NOT_AUTHORITATIVE`, `APPROVAL_MISSING`,
`BASE_HASH_MISMATCH`, `PROVIDER_UNREACHABLE`. Exit codes: 0 ok, 1 a check failed, 2 a
contract or usage error.
