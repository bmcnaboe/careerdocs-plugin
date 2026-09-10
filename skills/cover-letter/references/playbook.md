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

The plan leads with the highest-value evidence — direct evidence for `must` requirements
first — and fits a few paragraph units into the one-page budget. Anything over budget is
cut and reported; a letter should be short, so expect cuts.

## 3. Draft in voice

Write the letter as connected prose in the applicant's voice (`voice.md`):

- **Complement, do not repeat.** Do not paste résumé bullets. Add motivation, fit for the
  team, and context the résumé cannot carry.
- **Trace every claim** to a profile entity (the plan units' `source_ids`).
- **Be honest about gaps.** Never claim a gap requirement. If it matters, frame it as
  something you are growing into, or leave it out — never invent coverage.
- **Frame the letter.** The greeting is the first body unit, cited to the contact entity;
  the template carries the sign-off (`Sincerely,` on its allowlist, then the name).
- **Honor the approach.** When the brief carries an `approach`, its `letter_length`
  (`note`, roughly 150 to 200 words; `page`, roughly 300 to 400), `tone`, and `avoid`
  are the applicant's decisions; the page budget still governs.

## 4. Render

```sh
careerdocs render --kind cover_letter --pdf --role-slug <slug> --workspace <dir>
```

## 5. Check

```sh
careerdocs check applications/<slug>/outputs/<Name>-Cover-Letter.docx --workspace <dir>
```

Runs the standard checks, and the verbatim-bullet check: no résumé bullet may appear
word-for-word in the letter. Confirm every claim traces to a profile ID, no gap
requirement is claimed, and the letter fits its page budget.
