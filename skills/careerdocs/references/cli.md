# careerdocs CLI reference

Every command takes `--workspace <dir>` and `--json`. Paths below are relative to the
workspace.

## Commands

| Command | Does |
| --- | --- |
| `version` | plugin and profile-schema versions |
| `doctor` | workspace and how it resolved, config, profile size, templates, voice, identity, history mode (git or archive), LibreOffice, dependencies, template advisories |
| `config init` | write a default `careerdocs.json` if none exists |
| `config validate` | validate it; refuse credential or qualification content |
| `config workspace [<dir>]` | show how the workspace resolves, or record `<dir>` as the default and initialize it |
| `profile import <path>...` | register sources by sha256; return their text blocks and, for a LinkedIn CSV, draft candidates |
| `profile diff <file> [--flow f --subject s]` | build a ProfileDiff from candidates or operations; persist the questions it generates to state |
| `profile approve <diff_id> [--document <path>]` | record a hash-bound approval; `--document` also admits restricted entities into that document |
| `profile apply <diff_id>` | apply atomically; mark records citing changed entities stale |
| `profile validate` | validate the profile |
| `profile status` | list stale documents |
| `brief <jd.md> [--role-slug s]` | write `brief.json`: requirement skeletons, keywords, a positioning recommendation |
| `brief <brief.json> --validate` | validate a completed brief |
| `brief <brief.json> --coverage` | requirement keywords the visible profile lacks literally |
| `brief <brief.json> --alignment [--flow apply --subject s]` | the alignment questions the brief has not answered, with identity options |
| `map [--role-slug s]` | propose evidence and a classification per requirement into `map.json` |
| `map --validate <map.json>` | validate an edited map |
| `plan --kind resume\|cover_letter [--positioning m] [--page-budget n] [--sections ids] [--role-slug s]` | select and order evidence into `plan.<kind>.json` within the page budget; defaults come from the brief's `approach` |
| `plan --baseline --positioning m [--kind resume]` | a role-less plan from all visible evidence into `baselines/<m>/` |
| `render --kind k [--pdf] [--role-slug s \| --baseline --positioning m]` | fill the template; write the document, its PDF, and a record skeleton |
| `check <document>` | run the five checks, update the record; exit 1 on any failure |
| `commit -m "<msg>" (--role-slug s \| --baseline [--positioning m] \| --path p)...` | in a git workspace, commit that round's paths |
| `identity show`, `identity validate` | report or validate `identity.md` |
| `identity questions --flow onboard --subject s` | one question per missing identity section |
| `state show\|answer\|resume <flow> <subject>` | inspect state; `answer --question <id> --answer "<text>" [--text "<wording>"]` records an answer |

Flows: `onboard`, `update`, `apply`. A subject is the applicant's name for onboard and
update, the role slug for apply.

## Files the agent writes

**candidates.json** (import and update): `{"candidates": [...]}`. Each candidate has a
`type`, its fields, and one `provenance` `{source_id, method, recorded_at, actor,
excerpt}` (`method` extraction or statement, `actor` agent or applicant). Experiences,
skills, and education carry a `ref`; an achievement carries the `parent_ref` of its
experience or project. Candidates matching an existing entity's key become field updates.

**Answers become operations**: `{"operations": [{"op": "resolve_conflict", "id", "field",
"value"}, {"op": "update_field", "id", "field", "to"}, {"op": "set_visibility", "id",
"visibility"}, {"op": "retire_entity", "id", "reason"}]}`, diffed like candidates.

**brief.json**: `organization`, `role`, `seniority`, `location`, `requirements[]`
(`id`, `text`, `kind` must or nice, `keywords[]`), `keywords[]`,
`recommended_positioning`, `notes`; `approach` (`positioning`, `lead_evidence[]` entity
ids, `compress[]`, `resume_pages`, `sections[]` manifest ids, `letter_length` note or
page, `tone`, `avoid[]`, `notes`); `alignment` (`why`, `values[]`, `interests[]`, `focus`,
`through_line`, `lead_story`, `notes`).

**map.json**: one entry per requirement, `requirement_id`, `classification` direct,
transferable, or gap, `evidence[]` (`entity_id`, `why`), `note`. A gap has no evidence.

**plan.<kind>.json**: `units[]` with `unit_id`, `section_id`, `kind` (bullet, sentence,
field, subhead, labeled), `text`, `source_ids[]`, `emphasis`; `cuts[]` with `entity_id`
and `reason`. The agent rewrites `text` and keeps `source_ids` true.

## Entities

| Type | Required | Notable optional |
| --- | --- | --- |
| contact | `name` | `headline`, `location`, `email`, `phone`, `links[] {label, url}`; exactly one |
| experience | `organization`, `title`, `start_date` | `kind` employment (default), advising, board, volunteer; `end_date` (null = current), `location`, `summary` |
| achievement | `statement`, `parent_id` | `metrics[] {value, unit, context}` |
| education | `institution` | `degree`, `field_of_study`, `start_date`, `end_date`, `honors[]` |
| skill | `name` | `category`, `level` familiar, working, expert |
| project | `name` | `role`, `organization`, `start_date`, `end_date`, `summary`, `links[]` |
| credential | `name`, `issuer` | `issued_date`, `expires_date`, `url` |
| patent | `title`, `status` pending or granted | `number`, `filing_date`, `grant_date`, `url` |
| publication | `title` | `venue`, `date`, `url` |
| award | `title` | `issuer`, `date`, `description`, `url` |
| interest | `name` | `description` |
| affiliation | `organization` | `role`, `start_date`, `end_date`, `url` |

Every entity carries `visibility` (public, restricted, private), `verification`
(unverified, imported, applicant_verified, externally_verified), `provenance[]`, and
optional `conflicts[]`. Dates are `YYYY-MM-DD` or `YYYY-MM`; none may be in the future.
The JSON Schemas under `assets/schemas/` are authoritative.

## Checks

`check` writes each result (`pass`, `fail`, or `skipped` with a reason) into the record.

1. **factual**: every content line is a plan unit, an allowlisted template string, or a
   line the render composed from the brief and the date; every number traces to a cited
   entity. A cover letter also fails on any résumé bullet reproduced verbatim.
2. **links_dates**: dates parse, are ordered, and are not in the future; links are
   well-formed.
3. **extraction** (PDF): the PDF has a text layer.
4. **pagination** (PDF): a résumé matches its page target exactly; a letter fits its
   budget.
5. **layout** (PDF): content inside the margins, sane density, the contact line on one
   line; one PNG per page under `.careerdocs/layout/applications/<slug>/`.

Without LibreOffice the three PDF checks are skipped with a reason. Fix a failure at its
source, never by weakening a check.

## careerdocs.json

| Key | Default |
| --- | --- |
| `providers.markdown.path` | `profile` |
| `templates.dir`, `.resume`, `.cover_letter` | `templates`, `resume`, `cover-letter` |
| `voice.path`, `identity.path` | `voice/voice.md`, `identity/identity.md` |
| `outputs.applications_dir`, `.baselines_dir` | `applications`, `baselines` |
| `outputs.file_name` | `{name}-{org}-{role}-{kind}`; empty placeholders drop out |
| `outputs.history` | `auto` (git when the workspace is in a git work tree with a committer identity, else `archive`), `git`, or `archive` |
| `workflow.state_dir` | `.careerdocs/state` |
| `workflow.positioning_default` | `builder` |
| `workflow.page_budget.resume`, `.cover_letter` | `2`, `1` |

Keys or values that look like credentials (`password`, `token`, `api_key`, `secret`) or
qualifications (`entities`, `experience`, `skills`, `achievements`) are refused.
