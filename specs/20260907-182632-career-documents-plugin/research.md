# Research: Portable Resume and Cover-Letter Plugin

Every unknown in the plan's Technical Context resolved here, as Decision / Rationale /
Alternatives. Product names (Claude Code, Cowork, Codex, ChatGPT, Basic Memory) are the
ticket's targets, not choices made here.

## R1. Skill format and the single source

- **Decision**: The provider-neutral source is `skills/` at the repository root, one
  directory per skill, following the Agent Skills specification (`SKILL.md` with `name`
  and `description` frontmatter; optional `scripts/`, `references/`, `assets/`). Five
  skills: `career-documents` (core: schema, providers, checks, configuration, doctor)
  and the four flows `career-onboard`, `career-update`, `career-resume`,
  `career-cover-letter`.
- **Rationale**: Both target platforms load Agent Skills natively: Claude Code plugins
  auto-discover `skills/*/SKILL.md`, and Codex loads `$HOME/.agents/skills`. One format
  means zero translation, which is what "thin packages" requires.
- **Alternatives**: Slash commands per platform (rejected: two sources); a Python
  package with a CLI only (rejected: the interactive flows are agent-driven and need
  skill-level instructions, not just a binary).

## R2. Claude Code / Cowork package

- **Decision**: The repository root is the Claude plugin: `.claude-plugin/plugin.json`
  names the plugin, version, license, and repository; `.claude-plugin/marketplace.json`
  lists the single plugin with `source: "./"` so `claude plugin marketplace add
  bmcnaboe/career-documents` followed by `claude plugin install
  career-documents@career-documents` installs it, and Cowork installs from the same
  marketplace. `claude plugin validate .` is the structural verification.
- **Rationale**: Default component discovery reads `skills/` at the plugin root, which
  is exactly the shared source; the package is two manifests and no copies.
- **Alternatives**: A `packages/claude/` subtree with copied skills (rejected: copies
  drift; the inventory guard would only detect, not prevent).

## R3. ChatGPT / Codex package

- **Decision**: `packages/openai/` holds `manifest.json` (skill inventory and version)
  and an installer, `install.py` (Python standard library), that links or copies each
  `skills/career-*` directory into `$HOME/.agents/skills/` (Codex user scope, also read
  by ChatGPT-side skill upload flows) and prints the ChatGPT upload instructions. Each
  skill additionally carries `agents/openai.yaml` with display metadata and implicit
  invocation policy; Claude ignores that file.
- **Rationale**: Codex reads repo-level `.agents/skills` only locally and ChatGPT reads
  no repo-level skills, so the user-scope install is the one path that serves both.
  The installer is the only package-specific code and contains no flow logic.
- **Alternatives**: Committing `.agents/skills` symlinks in this repository (rejected:
  agent-layer's `.agents -> .claude` mirror already occupies that path here, and
  applicants do not run the flows inside this repository).

## R4. Runtime language and dependencies

- **Decision**: Python 3.11+. Repository tooling (gate, lints, guards) is standard
  library only. The runtime CLI `skills/career-documents/scripts/careerdocs.py`
  declares its third-party dependencies inline (PEP 723) and runs under `uv run`;
  `python3` with the listed packages installed by `pip` is the documented fallback.
  Dependencies: `docxtpl` (DOCX rendering), `pypdf` (PDF text and page count),
  `pdfplumber` (character positions for layout checks), `pypdfium2` (page rendering to
  PNG), `jsonschema` (schema validation), `python-dateutil` (date parsing).
- **Rationale**: uv is already the Spec Kit prerequisite, PEP 723 keeps the repository
  free of a package build, and every listed dependency ships wheels with no system
  libraries, so the checks run the same on every platform.
- **Alternatives**: Node (rejected: the applicant-side tooling in the target workspaces
  is Python; both agent platforms run Python readily); pure standard library
  (rejected: no PDF text extraction or DOCX templating without third-party code).

## R5. Profile serialization for the structured-Markdown reference provider

- **Decision**: A profile directory (default `profile/` in the applicant workspace)
  with `profile.md` (index: schema version, applicant reference, authoritative flag,
  provider) and one file per entity under `profile/<type>/<id>.md`. Each file is YAML
  frontmatter (every schema field) plus a Markdown body holding the human-readable
  statement. Sources are registered in `profile/sources.jsonl`; approvals in
  `profile/approvals.jsonl`.
- **Rationale**: One file per entity gives readable diffs, stable IDs in file names,
  and a shape Basic Memory can hold unchanged.
- **Alternatives**: One JSON file (rejected: unreadable diffs, merge conflicts); one
  Markdown file per type (rejected: entity-level provenance and visibility get lost in
  section text).

## R6. Basic Memory provider

- **Decision**: The Basic Memory provider writes the same per-entity notes into the
  configured vault project folder (default `career/`), as Basic Memory notes: the
  schema fields in frontmatter, the statement as `- [<type>] ...` observations, and
  links as `- part_of [[...]]` relations, so Basic Memory indexes them and the
  `write_note`, `read_note`, `search_notes`, and `build_context` tools work on them.
  Writes go to the vault files directly (Basic Memory watches its project folder);
  the agent uses the MCP tools for search and context, never as the only write path.
- **Rationale**: File-level writes keep the provider deterministic and testable
  without an MCP session, while the note conventions keep the vault first-class in
  Basic Memory. This is what lets Basic Memory be authoritative for an applicant while
  the structured-Markdown export stays a derived copy.
- **Alternatives**: MCP-only writes (rejected: untestable without a live server, and
  the agent would become the provider); storing the whole profile in one note
  (rejected: entity IDs and per-fact visibility need per-note frontmatter).

## R7. Identity, deduplication, precedence, and conflicts

- **Decision**: IDs are `<type>_<26-char ULID>`, generated once and immutable.
  Deduplication keys: experience by normalized organization plus title plus start
  year; education by institution plus degree; skill by normalized name; credential,
  patent, and publication by normalized title or number; achievement by normalized
  statement within its parent. Precedence for a contested attribute: applicant
  statement, then applicant-verified import, then newest import; a lower-precedence
  value never overwrites silently, it becomes a conflict candidate. A conflict blocks
  the attribute from documents until resolved.
- **Rationale**: Matches the ticket's stable-ID and conflict-rule requirements and
  gives the onboarding flow one deterministic question per conflict.
- **Alternatives**: Slug IDs from content (rejected: renames change them); last-write
  wins (rejected: silent overwrite of verified facts).

## R8. Reviewable diffs and approvals

- **Decision**: `careerdocs profile diff` emits a JSON diff (entity adds, field
  changes, conflict resolutions) plus a Markdown rendering; `careerdocs profile
  approve <diff-id>` records the applicant's approval in `approvals.jsonl` with the diff
  hash; `careerdocs profile apply <diff-id>` refuses without a matching approval. The
  agent records approval only after the applicant's explicit yes.
- **Rationale**: Approval is a durable, hash-bound record, so a resumed flow can prove
  what was approved.
- **Alternatives**: In-conversation approval only (rejected: not resumable, not
  auditable).

## R9. Document templates and rendering

- **Decision**: Templates are DOCX files rendered with `docxtpl` (Jinja placeholders
  inside the document) plus a sidecar `template.json` naming the placeholders, sections,
  page budget, and which entity types feed each section. The repository ships one
  sanitized example résumé template and one letter template; applicants own theirs.
- **Rationale**: The applicant's existing résumé design is a DOCX; docxtpl preserves
  its styles while the plugin owns only content, which keeps template and content as
  separate authorities.
- **Alternatives**: Markdown to DOCX conversion (rejected: loses the applicant's
  layout); HTML to PDF (rejected: no editable output).

## R10. PDF production and layout inspection

- **Decision**: `careerdocs render --pdf` converts with a local headless LibreOffice
  (`soffice`) when present; otherwise it reports that no converter is installed and
  the flow uses the platform's document tools to export, then continues with the
  checks on the resulting PDF. Layout inspection renders each page to PNG with
  `pypdfium2` for the agent to review and computes automated heuristics with
  `pdfplumber`: page count within budget, no page under a minimum text density, no
  characters outside the page margins.
- **Rationale**: LibreOffice is common but not guaranteed on applicant machines or in
  CI; the checks must not depend on it. The PNGs make the rendered layout inspectable
  on any platform that can view images.
- **Alternatives**: Requiring LibreOffice (rejected: CI and Cowork sandboxes lack it);
  skipping layout checks without a converter (rejected: silent skips are what the
  constitution forbids).

## R11. Factual traceability check

- **Decision**: The content plan records, for every rendered unit (bullet, sentence,
  header field), the profile IDs it draws on. `careerdocs check` extracts the document
  text, matches each extracted unit to a planned unit, and verifies that every number,
  date, organization, and title token in the unit occurs in the cited entities' text.
  Template-provided text (section headings, labels) is allowed through a per-template
  allowlist in `template.json`. Any unmatched unit or unsourced token fails the check
  and is named.
- **Rationale**: This is the deterministic anti-fabrication bar the ticket asks for:
  prose may be rephrased, facts may not be invented.
- **Alternatives**: LLM self-review only (rejected: not deterministic, not repeatable
  across platforms).

## R12. Link and date checks

- **Decision**: Dates must parse, be chronologically consistent, and not lie in the
  future; links must be well-formed and, when network access is available, answer a
  HEAD or GET with a non-error status. Offline runs record the link check as skipped
  with the reason rather than passing it.
- **Alternatives**: Skipping link checks entirely (rejected: dead links are the most
  common résumé defect).

## R13. Workflow state and resumability

- **Decision**: Each flow run persists `state.json` under the configured state
  directory (default `.career-documents/state/` in the workspace), keyed by flow and
  subject (applications by role slug). The state records every question asked with
  its answer, the pending diff, and every artifact path. Flows read the state before
  asking anything.
- **Alternatives**: Relying on conversation memory (rejected: not resumable across
  sessions or platforms).

## R14. Positioning

- **Decision**: Two named modes, `executive` and `builder`. Every experience,
  project, and achievement carries `positioning` tags; the content plan selects and
  orders by the chosen mode's tags and emphasis weights, never by editing facts.
- **Alternatives**: Free-text positioning (rejected: not testable).

## R15. Quality gate and guards

- **Decision**: `scripts/gate.sh basic|full|final`. basic: `pytest tests/unit` and the
  skills lint. full: basic plus `pytest tests/integration` (end-to-end CLI runs
  against `examples/`), the package inventory check, and the version-agreement check.
  final: full plus shellcheck, `gitleaks detect`, the applicant-data guard, and the
  agent-layer conformance check. The applicant-data guard (`scripts/pii_guard.py`)
  scans tracked files outside `examples/` and `tests/fixtures/` for email addresses
  (except `example.com`), telephone numbers (except `555`), and postal-address
  patterns. The verification-evidence guard
  (`scripts/verification_evidence_check.py`) fails when a spec acceptance scenario has
  no evidence row.
- **Rationale**: The constitution's principles I, IV, and V need mechanical enforcement.

## R16. Versioning

- **Decision**: One plugin version in `pyproject.toml` (`[project].version`); the
  Claude manifest, the OpenAI manifest, and each skill's `metadata.version` must equal
  it (`scripts/check_versions.py`). The profile schema carries its own version in the
  schema `$id` and in every profile's `schema_version`; a profile with a newer schema
  than the CLI understands is refused, an older one is migrated forward on the next
  approved write.

## R17. Testing without a converter in CI

- **Decision**: A PDF rendered once from the example résumé is committed under
  `tests/fixtures/rendered/` so pagination, extraction, and layout checks run in CI
  and on machines without LibreOffice; the DOCX-to-PDF step is exercised only where
  `soffice` exists and is reported as skipped elsewhere.
