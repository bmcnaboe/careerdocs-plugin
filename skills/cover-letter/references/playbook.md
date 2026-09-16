# Cover-letter playbook

Write a letter with a through-line of the applicant's own. `<dir>` below is the resolved
workspace (`doctor` shows it; `--workspace <dir>` only overrides it); artifacts live in
`applications/<role-slug>/`.

## 1. Reuse the brief, map, identity, and alignment

The résumé flow already produced `brief.json` and `map.json` for this role. Read them,
together with the identity profile (`identity.path`, default `identity/identity.md`) and
the brief's `alignment`. **Do not** re-run `brief` or `map`, and **do not** re-ask any
question the workflow state already answers.

If the brief has no `alignment` (the flow is running on its own, not through apply):

```sh
careerdocs brief applications/<slug>/brief.json --alignment --flow cover_letter --subject <slug> --workspace <dir> --json
```

lists the open questions — why this role, which values and interests it engages, the
focus it serves, the one idea the letter is organized around, the story that carries it —
with the identity's own values, interests, and direction as options, and any answer
already recorded. Ask them one at a time with a suggested answer, record each with
`state answer cover_letter <slug> --question <id> --answer "<text>"`, write the answers
to the brief under `alignment` (`why`, `values[]`, `interests[]`, `focus`,
`through_line`, `lead_story`, `notes`), and validate the brief. Without an identity
profile the questions still run; suggest the onboard skill's identity stage afterwards.

## 2. Plan the letter

```sh
careerdocs plan --kind cover_letter --positioning <executive|builder> --role-slug <slug> --workspace <dir> --json
```

The plan selects the highest-value evidence and carries `identity` and `alignment`. Use
the evidence to serve the through-line, not to cover requirements: the résumé carries
coverage. Answer the posting's application questions. Keep within the page budget and
report cuts.

## 3. Draft in voice

Write connected prose in the applicant's voice (`voice.md`), organized around the
alignment:

- **Open on the why.** The first body paragraph says why this role, in the words of
  `alignment.why`, and states the `through_line`. A reader should know in two sentences
  what this applicant wants and why it is this role.
- **Let one story carry it.** `alignment.lead_story` (from the identity profile's body or
  the map's evidence) is the letter's spine; two or three further pieces of evidence
  support it. Anything that does not serve the through-line goes to the résumé or out.
- **Let the identity show in the telling.** Values appear as what the applicant chose to
  do and why, personality in how it is said, motivations in what they are drawn to next.
  Never as a list of traits, never as self-praise.
- **Sound like a person.** Conversational first person, natural contractions, specific
  enthusiasm for the role and the organization's mission or customer value, a warm
  close. Résumé fragments and verb-first rules belong to the résumé.
- **Ground everything.** Qualifications in profile entities (`source_ids`), employer
  facts in the supplied role material, commitments and motives in the applicant's own
  answers (the identity and alignment). Never invent a mission, personal history,
  qualification, or learning activity, and never claim a gap requirement.
- **Honor the brief's `approach`**: `letter_length` (`note`, roughly 150–200 words;
  `page`, roughly 300–400), `tone`, and `avoid`, within the template's page budget.

The greeting is the first body unit, cited to the contact entity. The template carries
the sign-off (`Sincerely,` on its allowlist, then the name).

## 3b. Editorial review

Before rendering, read the draft aloud and compare it with the résumé, the sources, and
the identity. Revise when any of these is true; the CLI checks do not assess them:

- It walks the requirements: a paragraph per requirement, an "I have done X" per bullet.
- It could have been written by anyone with the same résumé: no why, no story, no value
  visible in a choice the applicant made.
- The through-line is missing, or arrives after the evidence instead of before it.
- Enthusiasm is generic ("excited about the opportunity"), phrasing is stiff or boastful,
  a claim is unsupported, or a sentence repeats the résumé without adding judgement.

## 4. Render

```sh
careerdocs render --kind cover_letter --pdf --role-slug <slug> --workspace <dir>
```

## 5. Check

```sh
careerdocs check applications/<slug>/outputs/<Name>-Cover-Letter.docx --workspace <dir>
```

Run the standard checks and separately confirm no résumé bullet appears word-for-word.
