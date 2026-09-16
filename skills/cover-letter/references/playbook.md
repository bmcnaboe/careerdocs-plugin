# Cover-letter playbook

Write a complementary cover letter. `<dir>` below is the resolved workspace (`doctor`
shows it; `--workspace <dir>` only overrides it); artifacts live in
`applications/<role-slug>/`.

## 1. Reuse the brief and map

The résumé flow already produced `brief.json` and `map.json` for this role. Read them.
**Do not** re-run `brief` or `map`, and **do not** re-ask any question that was answered
for the résumé — the workflow state already has the answers.

## 2. Plan the letter

```sh
careerdocs plan --kind cover_letter --positioning <executive|builder> --role-slug <slug> --workspace <dir> --json
```

Use the selected evidence to build a coherent story around the role's most important
needs. Answer the posting's application questions; let the résumé carry secondary detail.
Keep within the page budget and report cuts.

## 3. Draft in voice

Write connected prose in the applicant's voice (`voice.md`):

- Express specific enthusiasm for the role and the organization's mission or customer
  value. Personal motivation belongs when it explains the contribution the applicant
  is excited to make.
- Connect a few strong examples to the employer's needs, balancing supported requirements
  with natural flow. Add judgment, context, or collaboration beyond the résumé's facts.
- Sound like a pleasant, confident, humble prospective colleague: conversational first
  person, natural contractions, and a warm close. Apply letter-specific voice guidance;
  résumé fragments and verb-first rules belong to the résumé.
- Ground qualifications in profile entities (`source_ids`), employer facts in supplied
  role material, and commitments in applicant statements. Never invent a mission,
  personal history, qualifications, or learning activity to cover a gap.
- Honor the brief's `approach`: `letter_length` (`note`, roughly 150–200 words; `page`,
  roughly 300–400), `tone`, and `avoid`, within the template's page budget.

The greeting is the first body unit, cited to the contact entity. The template carries
the sign-off (`Sincerely,` on its allowlist, then the name).

Before rendering, read the draft aloud and compare it with the résumé and sources.
Revise weak enthusiasm, unclear contribution, stiff or boastful phrasing, unsupported
claims, and repetition that adds nothing. The CLI checks do not assess these qualities.

## 4. Render

```sh
careerdocs render --kind cover_letter --pdf --role-slug <slug> --workspace <dir>
```

## 5. Check

```sh
careerdocs check applications/<slug>/outputs/<Name>-Cover-Letter.docx --workspace <dir>
```

Run the standard checks and separately confirm no résumé bullet appears word-for-word.
