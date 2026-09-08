# Profile schema — `CareerProfile`

The authoritative qualification model, versioned and validated against
`assets/schemas/career-profile.schema.json` plus semantic rules the JSON Schema cannot
express. Dates are ISO 8601 (`YYYY-MM-DD`, or `YYYY-MM` when the day is unknown);
timestamps are RFC 3339 UTC. Every id is `<type>_<ULID>`.

## Index

| Field | Meaning |
| --- | --- |
| `schema_version` | semver of this schema |
| `applicant_ref` | opaque string; never a name |
| `authoritative_provider` | `markdown` or `basic_memory` |
| `derived` | `true` on every non-authoritative copy |
| `updated_at` | timestamp |
| `entities` | the `ProfileEntity[]` |
| `sources` | the `Source[]` ledger |

## Common entity fields

`id`, `type`, `visibility` (`public` / `restricted` / `private`), `verification`
(`unverified` / `imported` / `applicant_verified` / `externally_verified`),
`provenance[]` (≥1, append-only), optional `conflicts[]`, optional `positioning[]`
(`executive` / `builder`; empty = both), `tags[]`, `created_at`, `updated_at`.

## Entity types

- **contact** — `name` (required), `headline`, `location`, `email`, `phone`, `links[]`. One per profile.
- **experience** — `organization`, `title`, `start_date` (required); `employment_type`, `location`, `end_date` (null = current), `summary`, `achievement_ids[]`, `skill_ids[]`.
- **achievement** — `statement`, `parent_id` (required); `metrics[]`, `skill_ids[]`.
- **education** — `institution` (required); `degree`, `field_of_study`, `start_date`, `end_date`, `honors[]`.
- **skill** — `name` (required); `category`, `level` (`familiar` / `working` / `expert`), `evidence_ids[]`.
- **project** — `name` (required); `role`, `organization`, `start_date`, `end_date`, `summary`, `links[]`, `achievement_ids[]`.
- **credential** — `name`, `issuer` (required); `issued_date`, `expires_date`, `url`.
- **patent** — `title`, `status` (`pending` / `granted`) required; `number`, `filing_date`, `grant_date`, `url`.
- **publication** — `title` (required); `venue`, `date`, `url`.

## Provenance, conflict, source

- **Provenance**: `source_id`, `method` (`import` / `extraction` / `statement` / `resolution`), `recorded_at`, `actor`, optional `excerpt`.
- **Conflict**: `field`, `candidates[] { value, provenance }` (≥2), optional `resolution { value, resolved_at, by, note }`.
- **Source**: `source_id` (`src_<ULID>`), `kind` (`resume_docx` / `resume_pdf` / `network_export` / `note` / `url` / `statement`), `location`, optional `sha256`, `captured_at`.

## Semantic rules

- `end_date >= start_date` when both present; no date after today.
- `achievement.parent_id` resolves to an experience or project; every `*_ids[]` reference resolves.
- Exactly one contact.
- An **unresolved conflict blocks its field** from every rendered document.

## Precedence and deduplication

Match keys per type (experience `(org, title, start_year)`, education `(institution, degree)`,
skill `name`, credential/patent/publication `title`/`number`, achievement `statement` within
parent, contact singleton). When values differ, precedence is: an applicant **statement** >
an **applicant-verified** import > the **newest** import. The loser becomes a conflict
candidate; nothing is overwritten silently.

## Visibility on output

`private` never renders and never exports; `unverified` never renders; `restricted` renders
into a document only with a per-document approval; an unresolved conflict blocks its field.
A derived export drops `private` and is labeled `derived: true`.
