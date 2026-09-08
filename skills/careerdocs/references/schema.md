# Profile and configuration schema

The authoritative data structures, validated against the JSON Schemas shipped under
`assets/schemas/`. Dates are ISO 8601 (`YYYY-MM-DD`, or `YYYY-MM` when the day is
unknown); timestamps are RFC 3339 UTC. IDs are `<type>_<ULID>`.

## CareerProfile (`career-profile.schema.json`)

Index fields:

| Field                    | Meaning                                                        |
| ------------------------ | ------------------------------------------------------------- |
| `schema_version`         | semver of the profile schema                                  |
| `applicant_ref`          | opaque string; **never** a name                               |
| `authoritative_provider` | `markdown` or `basic_memory`                                  |
| `derived`                | `true` on every non-authoritative copy                        |
| `updated_at`             | timestamp                                                      |
| `entities`               | the `ProfileEntity[]`                                          |
| `sources`                | the `Source[]` ledger                                         |

### Common entity fields

Every entity carries `id`, `type`, `visibility` (`public` / `restricted` / `private`),
`verification` (`unverified` / `imported` / `applicant_verified` / `externally_verified`),
`provenance[]` (at least one, append-only), optional `conflicts[]`, optional
`positioning[]` (`executive` / `builder`; empty means both), `tags[]`, and
`created_at` / `updated_at`.

### Entity types

- **contact** — `name` (required), `headline`, `location`, `email`, `phone`, `links[]`.
  Exactly one contact per profile.
- **experience** — `organization`, `title`, `start_date` (required); `employment_type`,
  `location`, `end_date` (null = current), `summary`, `achievement_ids[]`, `skill_ids[]`.
- **achievement** — `statement`, `parent_id` (required, an experience or project);
  `metrics[] { value, unit, context }`, `skill_ids[]`.
- **education** — `institution` (required); `degree`, `field_of_study`, `start_date`,
  `end_date`, `honors[]`.
- **skill** — `name` (required); `category`, `level` (`familiar` / `working` / `expert`),
  `evidence_ids[]`.
- **project** — `name` (required); `role`, `organization`, `start_date`, `end_date`,
  `summary`, `links[]`, `achievement_ids[]`.
- **credential** — `name`, `issuer` (required); `issued_date`, `expires_date`, `url`.
- **patent** — `title`, `status` (`pending` / `granted`) required; `number`,
  `filing_date`, `grant_date`, `url`.
- **publication** — `title` (required); `venue`, `date`, `url`.

### Provenance, conflict, source

- **Provenance**: `source_id`, `method` (`import` / `extraction` / `statement` /
  `resolution`), `recorded_at`, `actor`, optional `excerpt`.
- **Conflict**: `field`, `candidates[] { value, provenance }` (at least two), optional
  `resolution { value, resolved_at, by, note }`.
- **Source**: `source_id` (`src_<ULID>`), `kind` (`resume_docx` / `resume_pdf` /
  `network_export` / `note` / `url` / `statement`), `location`, optional `sha256`,
  `captured_at`.

### Semantic rules (beyond the JSON Schema)

- `end_date >= start_date` when both are present.
- No date is after today.
- `achievement.parent_id` resolves to an experience or project; every `*_ids[]`
  reference resolves to an existing entity.
- Exactly one `contact`.
- An unresolved conflict blocks its field from every rendered document.

## careerdocs.json (`config.schema.json`)

Locates the four authorities; stores no qualifications or credentials.

| Key         | Content                                                                    |
| ----------- | ------------------------------------------------------------------------- |
| `version`   | config schema version (`"1"`)                                              |
| `providers` | `authoritative` (`markdown` / `basic_memory`), `markdown { path }`, `basic_memory { vault_path, project, folder }` |
| `templates` | `dir`, `resume`, `cover_letter`                                            |
| `voice`     | `path`                                                                     |
| `outputs`   | `applications_dir`, `baselines_dir`                                        |
| `workflow`  | `state_dir`, `positioning_default`, `page_budget { resume, cover_letter }`, `approval_mode` |

Forbidden anywhere in the file: credential-like keys or values (`password`, `token`,
`api_key`, `secret`) and qualification content (`entities`, `experience`, `skills`,
`achievements`). Every absent key takes its default.
