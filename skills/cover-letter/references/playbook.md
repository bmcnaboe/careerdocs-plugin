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

Write a brief note the applicant might send to a future colleague. Open with genuine
enthusiasm for this role and organization. Use one or two grounded supporting examples
to show how the applicant would help, letting identity shape the voice and details. The
link to the role may be implicit or stated plainly when natural; do not turn the posting
into a paragraph outline. Briefly identify an unfamiliar project at first mention; add
more detail only when it helps this application.

If the facts are clear but the person is missing, ask for one concrete moment that shows
how the applicant treats users or teammates. Ask one question at a time; use the answer
only if it serves this role.

Trace qualifications to profile entities (`source_ids`), employer details to the supplied
role material, and motives to the identity or recorded answers. Honor the brief's
`approach`, including length and things to avoid. The greeting is the first body unit,
cited to the contact entity; the template supplies the sign-off.

## 3b. Editorial review

Read the draft aloud. Each supporting detail should help the reader see the applicant
serving this role; clarify the connection naturally or cut the detail. Remove résumé
repetition, generic praise, and unsupported claims. When revising, keep the lines that
already work and change only what fails this review.

## 4. Render

```sh
careerdocs render --kind cover_letter --pdf --role-slug <slug> --workspace <dir>
```

## 5. Check

```sh
careerdocs check applications/<slug>/outputs/<Name>-Cover-Letter.docx --workspace <dir>
```

Run the standard checks and separately confirm no résumé bullet appears word-for-word.
