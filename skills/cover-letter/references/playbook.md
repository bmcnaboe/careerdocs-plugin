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
focus it serves, the one idea the letter is organized around, the thread of evidence
that best supports it —
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

One idea carries the letter: the alignment's through-line. Tell it as a short story the
applicant might tell a future colleague: each paragraph opens by picking up the last
thought of the one before it, never with a fresh topic, and never in the posting's
order. The résumé holds the facts, so the letter implies qualifications through one or
two examples chosen for the idea; a detail earns its place only when the reader needs it
for this role (a title or a headcount rarely does). Identify an unfamiliar project in a
few words at first mention. A gap the reader will notice is named once and turned toward
what the applicant brings to it, such as what they learn fast or where they do their best
work; never an apology. Length: `note` is 150 to 200 words, `page` 250 to 350.

If the facts are clear but the person is missing, ask for one concrete moment that shows
how the applicant treats users or teammates, one question at a time.

Trace qualifications to profile entities (`source_ids`), employer details to the supplied
role material, and motives to the identity or recorded answers. Honor the brief's
`approach`, including length and things to avoid. The greeting is the first body unit,
cited to the contact entity; the template supplies the role line, the date, and the
sign-off.

## 3b. Editorial review

Read the draft aloud. Cut any sentence a different applicant could have written, any
detail the role does not need, and any paragraph whose first sentence does not follow
from the one before it; cut until it reads as one argument. Keep the lines that already
work.

## 4. Render

```sh
careerdocs render --kind cover_letter --pdf --role-slug <slug> --workspace <dir>
```

Writes `<Name>-<Org>-<Role>-Cover.docx`. The template places the role line
(`<Role> at <Organization>`, from the brief) and today's date above the greeting and the
sign-off below the body; the record lists those two lines so the factual check allows
them. A previous render is kept the same way as a résumé's (committed in a git workspace,
archived otherwise).

## 5. Check

```sh
careerdocs check applications/<slug>/outputs/<Name>-<Org>-<Role>-Cover.docx --workspace <dir>
```

Run the standard checks and separately confirm no résumé bullet appears word-for-word.

## 6. Commit the round

```sh
careerdocs commit --role-slug <slug> -m "feat(<slug>): cover letter" --workspace <dir>
```

Commits the application folder and its state in a git workspace; a no-op elsewhere. Run
it after every generation and revision round.
