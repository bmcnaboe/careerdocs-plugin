# Provider Contract

A provider stores the authoritative `CareerProfile` or a derived copy. Providers are
selected by `career-documents.json` (`providers.authoritative`); exactly one is
authoritative. The contract is implemented by `careerdocs.providers.<name>` and exercised
by the `careerdocs profile` subcommands.

## Interface

| Operation                     | Input                                  | Output                                   | Rules                                                                                  |
| ----------------------------- | -------------------------------------- | ---------------------------------------- | -------------------------------------------------------------------------------------- |
| `read()`                      | none                                   | `CareerProfile`                          | Validates against the schema; refuses a newer `schema_version` than the CLI supports   |
| `hash()`                      | none                                   | content hash                             | Stable for identical content regardless of file order                                   |
| `propose(diff)`               | `ProfileDiff`                          | rendered Markdown + stored diff          | Never mutates the profile                                                              |
| `apply(diff_id, approval)`    | ids                                    | new `hash`                               | Refuses unless `approval.diff_hash` matches and `diff.base_hash == hash()`; atomic     |
| `export(target)`              | target provider spec                   | derived copy                             | Output carries `derived: true`; a derived copy can never be applied back               |
| `capabilities()`              | none                                   | `{ authoritative_ok, search, context }`  | Basic Memory reports `search` and `context`; Markdown reports neither                  |

## Structured Markdown (reference provider)

- Location: `providers.markdown.path` (default `profile/` in the workspace).
- Layout: `profile.md` index (frontmatter = `CareerProfile` index fields), `<type>/<id>.md` per entity (frontmatter = every entity field except the body statement; body = the statement or summary), `sources.jsonl`, `approvals.jsonl`, `diffs/<diff_id>.json`.
- Hash: SHA-256 over the canonical JSON of the sorted entity list plus the index.

## Basic Memory (first MCP provider)

- Location: `providers.basic_memory.vault_path` + `folder` (default `career/`), within the named Basic Memory `project`.
- Layout: the same per-entity files, written as Basic Memory notes: frontmatter `title` (human label), `type` (the entity type), `permalink` (`<folder>/<type>/<id>`), `tags`, plus every schema field; body `## Statement` (the text), `## Observations` with `- [<type>] <statement> #<id>` per rendered fact, `## Relations` with `- part_of [[<parent title>]]` and `- evidences [[<skill title>]]`.
- Writes are file writes to the vault; Basic Memory's watcher indexes them. The agent may use `search_notes` and `build_context` for retrieval and `schema_validate` for optional note validation. The MCP tools are never the only write path.
- Export: `export(markdown)` produces the structured-Markdown layout with `derived: true`.

## Precedence, deduplication, provenance, privacy, approved writes

- Deduplication and precedence: as defined in `data-model.md` (match keys per type; statement > applicant-verified import > newest import; losers become conflict candidates).
- Provenance: every operation in a diff carries provenance; `apply` appends, never replaces.
- Privacy: `export` and every renderer call `visible_for(document)`: `private` is always excluded; `restricted` requires an approval entry naming the document.
- Approved writes: only `apply` writes; only with a recorded approval; the approval file is append-only.

## Errors

Every operation raises a typed error with a machine code and a sentence: `SCHEMA_TOO_NEW`, `PROFILE_INVALID`, `NOT_AUTHORITATIVE`, `APPROVAL_MISSING`, `BASE_HASH_MISMATCH`, `PROVIDER_UNREACHABLE`. CLI exit code 2 for contract errors, 1 for check failures, 0 for success.
