# Templates and voice

Two of the four authorities are applicant-owned files: the document **templates** and the
**voice** profile. Both live in the workspace, never in this repository.

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
- `sections` — a list; each has `id`, `title`, and `units`. Each unit has `text`, `kind`
  (`bullet`, `field`, or `sentence`), `head` / `tail` (its first line split at the first
  tab), and `note` (any further lines). An experience unit is
  `Title, Organization<tab>Mar 2018 – Jun 2021`, so `head` is the role and `tail` the
  dates; when the section sets `role_summaries`, the role's summary follows on a second
  line and arrives as `note`. Other units have an empty `tail` and `note`.

A résumé section whose `entity_types` mix `experience` and `achievement` is planned
reverse-chronologically: each role, then its own achievements in emphasis order; an
achievement of a project is placed under the role at the project's organization.

The shipped example under `examples/applicant/templates/` (built by
`scripts/build_fixtures.py`) is a plain single-column design: centered name and contact
line, ruled section headings displayed in capitals, bold role lines with the dates on a
right tab stop, bulleted achievements, and, for the letter, a `Sincerely,` sign-off
followed by the name. Its résumé body:

```
{{ contact_name }}
{{ contact_details }}
{%p for section in sections %}
{%p if section.units %}
{{ section.title }}
{%p for unit in section.units %}
{%p if unit.kind == 'bullet' %}
{{ unit.text }}                          (a List Bullet paragraph)
{%p elif section.id == 'experience' %}
{{ unit.head }}<tab>{{ unit.tail }}      (bold role, date on a right tab stop)
{%p if unit.note %}
{{ unit.note }}                          (the role's summary, plain)
{%p endif %}
{%p else %}
{{ unit.text }}
{%p endif %}
{%p endfor %}
{%p endif %}
{%p endfor %}
```

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
| `sections[]` | `{ id, title, placeholder, entity_types[], max_items, required, kind?, role_summaries? }` — which entity types fill each section and how many; `kind` overrides the unit kind (e.g. `sentence` for a letter body); `role_summaries` adds each role's summary as a line under the role. Use the headings parsers recognise (Summary, Experience, Projects, Skills, Education, Patents, Publications, Certifications); `doctor` advises on any other |
| `allowlist[]` | template-provided strings (section titles, a sign-off, boilerplate) the factual check ignores |
| `style_notes` | free-form guidance |

Anything selected beyond a section's `max_items` or the global page budget is cut and
reported by `plan`.

## Voice profile — `voice.md`

An applicant-owned Markdown file (default `voice/voice.md`) with a frontmatter block the
renderer passes to the drafting step and the checks read. Fields: `version`, `person`
(first or third), `tense_rules`, `tone` (adjectives with examples), `preferred_terms[]`,
`banned_phrases[]`, `sentence_shape` (length, openers), `sample_sentences[]`. The drafting
step writes in this voice; the factual check keeps the prose honest, and banned phrases
should never appear. See `examples/applicant/voice/voice.md` for a sanitized example.
