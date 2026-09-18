# Templates and voice

Three of the five authorities are applicant-owned files: the document **templates**, the
**voice** profile, and the **identity** profile. All live in the workspace, never in this
repository.

## Document templates

A template is a folder under `templates.dir` (one per kind) holding a DOCX and a sidecar
manifest:

```
templates/resume/template.docx
templates/resume/template.json
templates/cover-letter/template.docx
templates/cover-letter/template.json
```

### `template.docx`

A [docxtpl](https://docxtpl.readthedocs.io/) template — a normal Word document whose
styles you control, with Jinja2 placeholders where content goes. The render context is:

- `{{ contact_name }}` and `{{ contact_details }}` — the two lines of the contact unit:
  the name, then location, phone, email, and links joined by ` · `. `{{ contact }}` is the
  same unit as one string with a newline between the lines.
- `{{ positioning }}` — the chosen mode.
- `{{ role_line }}` and `{{ date_line }}` — `<Role> at <Organization>` from the role
  brief (empty for a baseline) and today's date as `September 18, 2026`. A template that
  places them has them recorded with the render as `template_lines`, so the factual
  check allows them; the shipped letter places both, the shipped résumé neither.
- `sections` — a list; each has `id`, `title`, and `units`. Each unit has `text`, `kind`
  (`bullet`, `field`, `sentence`, `subhead`, or `labeled`), `head` / `tail` (its first
  line split at the first tab), `lead` / `rest` (the head split at the first ` — `, the
  rest keeping the dash), and `note` (any further lines). A dated unit — a role, a degree,
  an award, a credential, a publication, a patent, an affiliation — is
  `Title — Organization, Location<tab>Mar 2018 – Jun 2021`, so `lead` is the title,
  `rest` ` — Organization, Location`, and `tail` the dates; when the section sets
  `role_summaries`, a role's summary follows on a second line and arrives as `note`. A
  `subhead` is a project folded under its role (`Name — descriptor`); a `labeled` unit
  is `Label<tab>text`. Other units have an empty `tail` and `note`.

The shipped example under `examples/applicant/templates/` (built by
`scripts/build_fixtures.py`) is the plugin's default design, a plain single column in
Calibri with 0.7-inch margins: centered name and contact line; ruled section headings
displayed in capitals; a bold role with the organization and location muted and the dates
on a right tab stop, the role's summary beneath in italics; projects as italic sub-heads
under their role; bulleted achievements; bold-label skill lines; degrees, awards,
credentials, publications, and patents with the year on the right tab. Its résumé body:

```
{{ contact_name }}
{{ contact_details }}
{%p for section in sections %}
{%p if section.units %}
{{ section.title }}
{%p for unit in section.units %}
{%p if unit.kind == 'bullet' %}
{{ unit.text }}                                 (a List Bullet paragraph)
{%p elif unit.kind == 'subhead' %}
{{ unit.lead }}{{ unit.rest }}                  (bold italic name, muted descriptor)
{%p elif unit.kind == 'labeled' and unit.tail %}
{{ unit.head }}  {{ unit.tail }}                (bold label, then the text)
{%p elif unit.kind == 'field' and unit.tail and section.id == 'experience' %}
{{ unit.lead }}{{ unit.rest }}<tab>{{ unit.tail }}   (bold role, muted organization, dates)
{%p if unit.note %}
{{ unit.note }}                                 (the role's summary, italic)
{%p endif %}
{%p elif unit.kind == 'field' and unit.tail %}
{{ unit.lead }}{{ unit.rest }}<tab>{{ unit.tail }}   (bold lead, the year on the right)
{%p else %}
{{ unit.text }}
{%p endif %}
{%p endfor %}
{%p endif %}
{%p endfor %}
```

The letter shares the header, then places `{{ role_line }}` (centered, bold), the
`{{ date_line }}`, the body units, and a `Sincerely,` sign-off followed by the name.

Links need no placeholder: every link the profile holds (contact and project links, patent
URLs, the contact email) is planned as its bare display form (`linkedin.com/in/handle`) and,
after rendering, wrapped in a real hyperlink to the full URL with the run's own formatting,
so the DOCX and the PDF are clickable and the visible text still matches the plan.

Keep the styling (fonts, spacing, margins) in the DOCX; the plugin replaces only the
placeholder content. Two rules keep a restyled template compatible with the checks: every
paragraph the template adds on its own (a sign-off, boilerplate) goes on the manifest's
`allowlist`, because the factual check treats any other line as unsourced; and headings
shown in capitals use the all-caps font property rather than uppercase text, so the
extracted title still matches the allowlist.

### `template.json`

The manifest that drives selection and the checks:

| Field | Meaning |
| --- | --- |
| `name`, `version` | recorded in every output record |
| `kind` | `resume` or `cover_letter` |
| `page_budget` | pages; drives the pagination check and the plan's global cut cap |
| `units_per_page` | rough capacity used with `page_budget` |
| `sections[]` | `{ id, title, placeholder, entity_types[], max_items, required, kind?, role_summaries?, experience_kinds?, group_by?, join? }` — which entity types fill each section and how many; `kind` overrides the unit kind (`sentence` for a letter body, `labeled` for skill lines); `role_summaries` adds each role's summary as a line under the role; `experience_kinds` limits a section's roles to those kinds (`employment`, `advising`, `board`, `volunteer`; absent means every kind); `group_by` merges the section's units into one `Label<tab>a, b, c` line per distinct value of an entity field (skills by `category`); `join` merges them into one line with that separator (interests). Use the headings parsers recognise (Summary, Experience, Projects, Skills, Technical Focus, Education, Certifications, Patents, Publications, Awards, Affiliations, Volunteer Experience, Interests); `doctor` advises on any other |
| `allowlist[]` | template-provided strings (section titles, a sign-off, boilerplate) the factual check ignores |
| `style_notes` | free-form guidance |

Two placeholders are special. `contact` marks the header section. `summary` marks a
section with no entities of its own: the plan emits one drafted sentence unit whose text
starts as the contact's headline and whose sources are the lead evidence (the approach's
`lead_evidence` when the brief names it, else the strongest cited entities of the
section's `entity_types`), for the drafting step to write the summary those entities
support.

A résumé section that lists `experience` and `achievement` is planned
reverse-chronologically: each role, then its own achievements in emphasis order. When it
also lists `project`, the projects at a role's organization follow that role as
sub-heads, each with its achievements, and a project at no held role is left for a later
section that lists projects. Every section is optional except the header and Experience,
and one manifest serves every role: the brief's `approach.sections` (or `plan
--sections`) names the sections one résumé uses — a Technical Focus for a technical role,
Awards or Interests for an executive one — and a one-page résumé is the same design with
fewer sections and units. Anything selected beyond a section's `max_items` or the global
page budget is cut and reported by `plan`.

## Voice profile — `voice.md`

An applicant-owned Markdown file (default `voice/voice.md`) that the agent reads when
drafting. Frontmatter fields: `version`, `person`
(first or third), `tense_rules`, `tone` (adjectives with examples), `preferred_terms[]`,
`banned_phrases[]`, `sentence_shape` (length, openers), `sample_sentences[]`. The drafting
step follows these preferences and checks claims against their sources. Use the Markdown
body for document-specific guidance: résumé bullets can be verb-first while letters
sound conversational, warm, and enthusiastic. See `examples/applicant/voice/voice.md`
for a sanitized example. The CLI checks do not evaluate voice; the cover-letter flow
includes an editorial review before rendering.

## Identity profile — `identity.md`

An applicant-owned Markdown file (default `identity/identity.md`, `identity.path`) that
holds who the applicant is beyond the facts, so a cover letter has a through-line of
their own instead of a walk through the requirements. Frontmatter (JSON, validated by
`careerdocs identity validate` against `identity.schema.json`):

| Field | Meaning |
| --- | --- |
| `version` | `"1"` |
| `values[]` | `{ name, statement }` — what they care about in work, each with what it looks like in practice |
| `personality[]` | `{ trait, example }` — how colleagues experience them |
| `motivations[]` | what energizes them, and what drains them |
| `working_style` | how they like to work |
| `career_focus` | `{ direction, roles[], settings[], avoid[] }` — where the career is heading |
| `interests[]` | the problems, domains, or technologies they are drawn to now |

The first four are durable; career focus and interests are the baseline each application
refines. The Markdown body holds the stories the applicant tells about themselves and
notes on how to use them. The onboard flow captures all of it by interview
(`careerdocs identity questions` asks only for the sections still missing) and writes the
file after the applicant approves the draft. It is never a source of qualifications: every
fact a letter states still traces to a profile entity.

Per application, the brief's `alignment` records how one role connects to the identity —
`why`, `values[]`, `interests[]`, `focus`, `through_line`, `lead_story`, `notes` — captured
by the apply flow (or the cover-letter flow on its own) through
`careerdocs brief --alignment`, which asks only what the brief lacks. The letter plan
carries the identity path and the alignment, and the output record names the identity
profile beside the voice. See `examples/applicant/identity/identity.md` for a sanitized
example.
