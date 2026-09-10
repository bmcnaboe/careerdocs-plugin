# Apply playbook

Run one application end to end. `<dir>` below is the resolved workspace (`doctor` shows
it); the application folder is `applications/<slug>/`; the workflow state is flow `apply`,
subject `<slug>`. Each stage ends by recording its answer, so `state resume apply <slug>`
picks up an interrupted run at the right stage. Ask each question with a suggested
answer; a bare yes accepts it.

## 0. Resume or start

```sh
careerdocs state resume apply <slug> --workspace <dir> --json
```

If a state exists, continue from its step; answered questions are not asked again.

## 1. The role

Obtain the posting: pasted text is written to `applications/<slug>/job-description.md`;
a file is copied there; for a URL, the applicant pastes the text (the plugin fetches
nothing). Propose the slug as `<organization>-<role>` in lowercase hyphens. Then the
résumé playbook's brief step:

```sh
careerdocs brief applications/<slug>/job-description.md --role-slug <slug> --workspace <dir> --json
```

Complete organization, role, seniority, and location. When the posting has no
"requirements" heading the skeleton has no requirements: author them from the posting,
one per line of the "what you'll own" and "profile" sections, must or nice, with
keywords. Validate with `brief --validate`. Confirm the organization, role, and slug in
one exchange and record it:

```sh
careerdocs state answer apply <slug> --question role --text "Organization, role, slug" --answer "<org> — <role> (<slug>)" --workspace <dir>
```

## 2. Fit and gaps

The résumé playbook's map and coverage steps:

```sh
careerdocs map --role-slug <slug> --workspace <dir> --json
careerdocs map --validate applications/<slug>/map.json --workspace <dir>
careerdocs brief applications/<slug>/brief.json --coverage --workspace <dir> --json
```

Judge every classification yourself (direct, transferable, gap) before validating. Then
show one screen: the counts, the must requirements that are gaps or transferable, and
the missing keywords in three groups — synonyms of evidence the profile already holds
(these are reworded with the posting's term when drafting, never added), qualifications
the applicant may genuinely hold, and posting prose with no fact behind it (ignored).
Ask one question — which of the second group do you genuinely have? — and record it:

```sh
careerdocs state answer apply <slug> --question gaps --text "Confirmed qualifications" --answer "<list, or none>" --workspace <dir>
```

For each confirmed qualification run the `update` skill exactly as its playbook says:
the statement as a source, candidates, `profile diff --flow update --subject <name>`,
the rendered diff shown, an explicit yes, approve, apply. Then run `map` again and
re-validate, since new evidence changes the classifications.

## 3. The approach

Propose, in one short list with a default for each item, and confirm in one exchange:

- **positioning** — the brief's recommendation and why; the applicant's standing
  positioning notes override a weak signal.
- **lead_evidence** — the three entities with the highest value in the map (direct
  evidence for must requirements first), as ids with a one-line label each.
- **compress** — roles, sections, or projects to compress or leave out for this role.
- **resume_pages** — the template's budget, or 1 when a one-page résumé suits the role.
- **letter_length** — `note` (a brief note, roughly 150 to 200 words) or `page` (a full
  page, roughly 300 to 400 words); `note` when the posting asks for a note.
- **tone** — drawn from `voice.md` (person, tone adjectives) and the posting's register,
  for example "direct and warm, first person".
- **avoid** — topics, phrases, or facts to keep out of both documents.

Write the agreed values to `brief.json` under `approach`, validate the brief, and record
the exchange:

```sh
careerdocs brief applications/<slug>/brief.json --validate --workspace <dir>
careerdocs state answer apply <slug> --question approach --text "Agreed approach" --answer "<one-line summary>" --workspace <dir>
```

## 4. The documents

**Résumé** — the résumé playbook from its plan step. `plan` reads positioning and
`resume_pages` from the brief's approach (`--positioning` and `--page-budget` override):

```sh
careerdocs plan --kind resume --role-slug <slug> --workspace <dir> --json
```

Draft in voice with the lead evidence first, compressing or omitting what `compress`
names and keeping `avoid` out; render with `--pdf`; check. Record the document path:

```sh
careerdocs state answer apply <slug> --question resume --text "Résumé document" --answer "<path>" --workspace <dir>
```

**Cover letter** — the cover-letter playbook from its plan step, honoring
`letter_length`, `tone`, and `avoid`; render; check, including the verbatim-bullet check.
Record the path under question `letter`.

## 5. The report

Tell the applicant, in one screen: what the résumé plan cut for space (`plan.cuts`),
which requirements remain honest gaps, which qualifications were confirmed and added,
and the two document paths. `profile status` names any earlier document the new facts
made stale.
