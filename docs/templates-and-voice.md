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

- `{{ contact }}` — the contact line.
- `{{ positioning }}` — the chosen mode.
- `sections` — a list; each has `title` and `units`, and each unit has `text` and `kind`.

A minimal body loops over sections and their units:

```
{{ contact }}
{%p for section in sections %}
{{ section.title }}
{%p for unit in section.units %}
{{ unit.text }}
{%p endfor %}
{%p endfor %}
```

Keep the styling (fonts, spacing, margins) in the DOCX; the plugin replaces only the
placeholder content.

### `template.json`

The manifest that drives selection and the checks:

| Field | Meaning |
| --- | --- |
| `name`, `version` | recorded in every output record |
| `kind` | `resume` or `cover_letter` |
| `page_budget` | pages; drives the pagination check and the plan's global cut cap |
| `units_per_page` | rough capacity used with `page_budget` |
| `sections[]` | `{ id, title, placeholder, entity_types[], max_items, required, kind? }` — which entity types fill each section and how many; `kind` overrides the unit kind (e.g. `sentence` for a letter body) |
| `allowlist[]` | template-provided strings (section titles, boilerplate) the factual check ignores |
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
