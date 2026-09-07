# Data Model: Portable Resume and Cover-Letter Plugin

All persisted structures are JSON-serializable and validated against the schemas under
`skills/career-documents/assets/schemas/` (the contract drafts live in `contracts/`). Dates are ISO 8601 (`YYYY-MM-DD`,
or `YYYY-MM` when the day is unknown); timestamps are RFC 3339 UTC.

## Identity and common fields

Every `ProfileEntity` carries:

| Field           | Type                                                                | Rules                                                                 |
| --------------- | ------------------------------------------------------------------- | --------------------------------------------------------------------- |
| `id`            | string `<type>_<ULID>`                                              | Generated once, immutable, unique across the profile                  |
| `type`          | enum                                                                | `contact`, `experience`, `achievement`, `education`, `skill`, `project`, `credential`, `patent`, `publication` |
| `visibility`    | enum `public` / `restricted` / `private`                            | `private` never renders; `restricted` needs per-document approval     |
| `verification`  | enum `unverified` / `imported` / `applicant_verified` / `externally_verified` | `unverified` facts never render                              |
| `provenance`    | `Provenance[]` (min 1)                                              | Append-only                                                            |
| `conflicts`     | `Conflict[]`                                                        | An unresolved conflict blocks the affected field from rendering       |
| `positioning`   | enum[] of `executive` / `builder`                                   | Empty means both                                                       |
| `tags`          | string[]                                                            | Free-form, applicant-owned                                             |
| `created_at`, `updated_at` | timestamp                                                |                                                                        |

### Provenance

| Field         | Type                                                     |
| ------------- | -------------------------------------------------------- |
| `source_id`   | reference to `Source.source_id`                          |
| `method`      | enum `import` / `extraction` / `statement` / `resolution` |
| `recorded_at` | timestamp                                                |
| `actor`       | string (`applicant`, or the agent identity)              |
| `excerpt`     | optional string, the source text the fact came from      |

### Conflict

| Field        | Type                                                          |
| ------------ | ------------------------------------------------------------- |
| `field`      | string, the entity attribute in dispute                       |
| `candidates` | `{ value, provenance: Provenance }[]` (min 2)                 |
| `resolution` | optional `{ value, resolved_at, by, note }`                   |

## Entity types

- **contact**: `name`, `headline`, `location`, `email`, `phone`, `links[] { label, url }`. Exactly one per profile.
- **experience**: `organization`, `title`, `employment_type`, `location`, `start_date`, `end_date` (null = current), `summary`, `achievement_ids[]`, `skill_ids[]`.
- **achievement**: `statement`, `metrics[] { value, unit, context }`, `parent_id` (experience or project), `skill_ids[]`.
- **education**: `institution`, `degree`, `field_of_study`, `start_date`, `end_date`, `honors[]`.
- **skill**: `name`, `category`, `level` (enum `familiar` / `working` / `expert`), `evidence_ids[]`.
- **project**: `name`, `role`, `organization` (optional), `start_date`, `end_date`, `summary`, `links[]`, `achievement_ids[]`.
- **credential**: `name`, `issuer`, `issued_date`, `expires_date` (optional), `url` (optional).
- **patent**: `title`, `number` (optional until granted), `status` (enum `pending` / `granted`), `filing_date`, `grant_date` (optional), `url` (optional).
- **publication**: `title`, `venue`, `date`, `url` (optional).

Validation rules: `end_date >= start_date` when both present; no date after today; `achievement.parent_id` must resolve to an experience or project; every `*_ids[]` reference must resolve; `contact` is required and unique.

## CareerProfile (index)

| Field                   | Type                                     |
| ----------------------- | ---------------------------------------- |
| `schema_version`        | string, semver of `career-profile.schema.json` |
| `applicant_ref`         | opaque string, never a name              |
| `authoritative_provider`| enum `markdown` / `basic_memory`         |
| `derived`               | boolean, true on every non-authoritative copy |
| `updated_at`            | timestamp                                |
| `entities`              | `ProfileEntity[]`                        |
| `sources`               | `Source[]`                               |

### Source

| Field         | Type                                                                        |
| ------------- | --------------------------------------------------------------------------- |
| `source_id`   | string `src_<ULID>`                                                         |
| `kind`        | enum `resume_docx` / `resume_pdf` / `network_export` / `note` / `url` / `statement` |
| `location`    | path or URI (workspace-relative when a path)                                 |
| `sha256`      | optional, for files                                                          |
| `captured_at` | timestamp                                                                    |

## Deduplication and precedence (from research R7)

- Match keys per type: experience `(norm(organization), norm(title), start_year)`; education `(norm(institution), norm(degree))`; skill `norm(name)`; credential, patent, publication `norm(title)` or `number`; achievement `norm(statement)` within `parent_id`; contact singleton.
- Precedence when values differ: `statement` (applicant) > `applicant_verified` import > newest import. A lower-precedence value becomes a conflict candidate; nothing overwrites silently.

## Diff and approval

- **ProfileDiff**: `diff_id` (`diff_<ULID>`), `base_hash` (hash of the profile it applies to), `operations[]` of `add_entity { entity }`, `update_field { id, field, from, to, provenance }`, `resolve_conflict { id, field, value }`, `set_visibility { id, visibility }`, `retire_entity { id, reason }`; `summary_md` (the human rendering).
- **Approval**: `diff_id`, `diff_hash`, `approved_at`, `by`, `scope` (`all` or an operation subset). `apply` requires an approval whose `diff_hash` matches and whose `base_hash` matches the current profile; otherwise it refuses with the reason.

## Workspace configuration (`career-documents.json`)

| Key         | Content                                                                                   |
| ----------- | ----------------------------------------------------------------------------------------- |
| `version`   | config schema version                                                                      |
| `providers` | `authoritative` (`markdown` / `basic_memory`), `markdown { path }`, `basic_memory { vault_path, project, folder }` |
| `templates` | `dir`, `resume`, `cover_letter` (template directory names)                                 |
| `voice`     | `path` to the voice profile                                                                |
| `outputs`   | `applications_dir`, `baselines_dir`                                                        |
| `workflow`  | `state_dir`, `positioning_default`, `page_budget { resume, cover_letter }`, `approval_mode` (`explicit` only in MVP) |

Forbidden anywhere in the file: keys or values that look like credentials (`password`, `token`, `api_key`, `secret`) or qualification content (`entities`, `experience`, `skills`, `achievements`). Defaults apply for every absent key.

## VoiceProfile (applicant-owned Markdown with frontmatter)

`version`, `person` (first or third), `tense_rules`, `tone` (adjectives with examples), `preferred_terms[]`, `banned_phrases[]`, `sentence_shape` (length, openers), `sample_sentences[]`. The renderer passes the voice profile to the drafting agent and the check verifies banned phrases are absent.

## DocumentTemplate

`template.json` next to the DOCX: `name`, `kind` (`resume` / `cover_letter`), `version`, `page_budget`, `sections[] { id, placeholder, entity_types[], max_items, required }`, `allowlist[]` (template-provided strings the traceability check ignores), `style_notes`.

## Application artifacts (per role, under `outputs.applications_dir/<role-slug>/`)

- **RoleBrief** (`brief.json`): `organization`, `role`, `seniority`, `location`, `source` (`Source`), `requirements[] { id, text, kind (must / nice), keywords[] }`, `keywords[]`, `recommended_positioning`, `notes`.
- **RequirementEvidenceMap** (`map.json`): per requirement `{ requirement_id, classification (direct / transferable / gap), evidence[] { entity_id, why }, note }`.
- **ContentPlan** (`plan.json`): `positioning`, `template`, `voice`, `page_budget`, `units[] { unit_id, section_id, kind (bullet / sentence / field), text, source_ids[], emphasis }`, `cuts[] { entity_id, reason }`.
- **OutputRecord** (`outputs/<file>.record.json`): `document` (path), `kind`, `generated_at`, `plugin_version`, `schema_version`, `role_brief` (path), `map` (path), `content_plan` (path), `template { name, version }`, `voice { version }`, `positioning`, `source_ids[]`, `checks { factual, links_dates, extraction, pagination, layout } → { status (pass / fail / skipped), details }`, `stale` (boolean, set by the update flow), `stale_reason`.

## WorkflowState (`workflow.state_dir/<flow>/<subject>.json`)

`flow` (`onboard` / `update` / `resume` / `cover_letter`), `subject`, `started_at`, `updated_at`, `step`, `questions[] { id, text, answer, answered_at }`, `pending_diff_id`, `artifacts { name: path }`, `completed_at`.

## State transitions

- Entity verification: `unverified → imported` (import with provenance) `→ applicant_verified` (applicant statement or conflict resolution) `→ externally_verified` (documented external check). Never backwards except by an approved diff that records why.
- Conflict: `open → resolved` by exactly one resolution; a resolved conflict stays in history.
- OutputRecord: `fresh → stale` when an approved diff changes any `source_ids` entity; `stale → fresh` only by regenerating.
- WorkflowState: `started → awaiting_answers → awaiting_approval → applied → completed`; any step may resume from persisted state.
