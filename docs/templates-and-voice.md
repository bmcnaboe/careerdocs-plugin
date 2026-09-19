# Templates, voice, and identity

Three of the five authorities are files you own, in your workspace: the document
templates, the voice profile, and the identity profile. The onboard skill sets up all
three; this page is for changing them afterwards.

## Templates

One folder per document kind, each with a DOCX and a manifest:

```
templates/resume/template.docx
templates/resume/template.json
templates/cover-letter/template.docx
templates/cover-letter/template.json
```

The plugin ships a default design under `examples/applicant/templates/`: a plain single
column in Calibri with 0.7-inch margins, a centered name and contact line, ruled
capitalized headings, a bold role with the organization muted and the dates on a right
tab, an italic descriptor under the role, projects as italic sub-heads under their role,
bulleted achievements, bold-label skill lines, and dated lines with the year on the
right. The letter shares the header, then places the role line, the date, the body, and
a sign-off. You can restyle the DOCX freely (fonts, spacing, margins, colors); the plugin
replaces only the placeholder content.

### The DOCX

A [docxtpl](https://docxtpl.readthedocs.io/) template: a Word document with Jinja2
placeholders. The render context:

- `{{ contact_name }}` and `{{ contact_details }}`: the two lines of the contact unit.
- `{{ role_line }}` and `{{ date_line }}`: `<Role> at <Organization>` from the brief and
  today's date. A template that places them has them recorded with the render so the
  factual check allows them; the shipped letter places both, the résumé neither.
- `sections`: a list of `{ id, title, units }`. Each unit has `text`, `kind` (`bullet`,
  `field`, `sentence`, `subhead`, `labeled`), `head` and `tail` (the first line split at
  its tab: a role and its dates, a label and its text), `lead` and `rest` (the head split
  at the first ` — `), and `note` (any further lines, such as a role's summary).

The shipped résumé body, in outline:

```
{{ contact_name }}
{{ contact_details }}
{%p for section in sections %}{%p if section.units %}
{{ section.title }}
{%p for unit in section.units %}
{%p if unit.kind == 'bullet' %}{{ unit.text }}                          (List Bullet)
{%p elif unit.kind == 'subhead' %}{{ unit.lead }}{{ unit.rest }}         (bold italic, muted descriptor)
{%p elif unit.kind == 'labeled' and unit.tail %}{{ unit.head }}  {{ unit.tail }}   (bold label)
{%p elif unit.kind == 'field' and unit.tail %}{{ unit.lead }}{{ unit.rest }}<tab>{{ unit.tail }}
{%p if unit.note %}{{ unit.note }}{%p endif %}                            (italic summary)
{%p else %}{{ unit.text }}{%p endif %}
{%p endfor %}{%p endif %}{%p endfor %}
```

Links need no placeholder: every link in the profile is written as its bare display form
and turned into a real hyperlink after rendering, so the DOCX and PDF are clickable.

Two rules keep a restyled template compatible with the checks: every fixed string the
template adds (a sign-off, boilerplate) goes on the manifest's `allowlist`, because the
factual check treats any other line as unsourced; and headings shown in capitals use the
all-caps font property rather than uppercase text, so the extracted title still matches.

### The manifest

| Field | Meaning |
| --- | --- |
| `name`, `version`, `kind` | recorded in every output record; `resume` or `cover_letter` |
| `page_budget`, `units_per_page` | pages, and the rough capacity used to plan them |
| `sections[]` | `{ id, title, placeholder, entity_types[], max_items, required, kind?, role_summaries?, experience_kinds?, group_by?, join? }` |
| `allowlist[]` | template-provided strings the factual check ignores |
| `style_notes` | free-form guidance for the drafting step |

Within `sections[]`, `kind` overrides the unit kind (`sentence` for a letter body,
`labeled` for skill lines); `role_summaries` adds each role's summary as a line under it;
`experience_kinds` limits a section to `employment`, `advising`, `board`, or `volunteer`
roles; `group_by` merges the section into one `Label<tab>a, b, c` line per value of an
entity field (skills by `category`); `join` merges it into one line (interests). Use
headings résumé parsers recognise (Experience, Projects, Skills, Technical Focus,
Education, Certifications, Patents, Publications, Awards, Affiliations, Volunteer
Experience, Interests); `doctor` advises on any other. The placeholder `contact` marks the
header and `summary` marks the drafted summary. Every section is optional except the
header and Experience; the approach's `sections` picks the ones a role uses, and a section
with no evidence does not render.

## The voice profile

`voice/voice.md`: a JSON frontmatter block, then a Markdown body.

| Field | Meaning |
| --- | --- |
| `person` | `first` or `third` |
| `tense_rules` | when to use past and present |
| `tone[]` | `{ adjective, example }` |
| `preferred_terms[]`, `banned_phrases[]` | words to reach for, words never to use |
| `sentence_shape` | `{ max_words, openers[] }` |
| `sample_sentences[]` | lines that sound like you |

The body holds document-specific guidance: résumé bullets can be verb-first while letters
sound conversational and warm. See `examples/applicant/voice/voice.md`.

## The identity profile

`identity/identity.md`: who you are beyond the facts, so a letter has a through-line of
your own. JSON frontmatter, validated by `careerdocs identity validate`:

| Field | Meaning |
| --- | --- |
| `values[]` | `{ name, statement }` |
| `personality[]` | `{ trait, example }` |
| `motivations[]` | what energizes you, and what drains you |
| `working_style` | how you like to work |
| `career_focus` | `{ direction, roles[], settings[], avoid[] }` |
| `interests[]` | the problems and domains you are drawn to now |

The body holds the stories you tell about yourself. Values, personality, motivations,
and working style change rarely; career focus and interests are worth revisiting, which
`onboard` does on a later run. The identity is never a source of qualifications: every
fact a letter states still traces to your profile. See
`examples/applicant/identity/identity.md`.
