---
name: apply
description: Produce the application for one job posting through a short guided interview, either the tailored résumé, the cover letter, or both. Use when the applicant has an onboarded profile and a posting, or asks to tailor a résumé, write a cover letter, or apply to a role. It builds the role brief and requirement map, shows the fit and the keywords the profile lacks, records qualifications they confirm, agrees an approach (positioning, lead evidence, what to compress, length, tone), settles the role alignment for the letter, then drafts, renders, and checks each document and reports the cuts and gaps. Every question carries a suggested answer so a yes moves on; nothing enters the profile without an explicit approval; a gap is never claimed. Resumable.
license: MIT
compatibility: "Python 3.10+; uv recommended. Requires the careerdocs core skill, an onboarded profile, templates, and voice. Optional LibreOffice for PDF output and the PDF checks."
metadata:
  version: "0.6.0"
  author: "careerdocs-plugin contributors"
---

# apply

One posting in; a checked résumé, cover letter, or both out, through a short interview.
Read the core `careerdocs` skill first; commands and file shapes are in its
`references/cli.md`. Every question carries a suggested answer so a bare yes moves on,
and nothing the workflow state already answers is asked again. State lives under flow
`apply`, subject `<slug>`; `state resume apply <slug>` continues an interrupted run.
Record each stage's answer with `state answer apply <slug> --question <id> --answer "..."`.

## 1. The role

Save the posting (pasted text, a file, or text pasted from a URL; the plugin fetches
nothing) as `applications/<slug>/job-description.md`, slug `<organization>-<role>` in
lowercase hyphens. Run `brief <that file> --role-slug <slug>` and complete the
organization, role, seniority, and location. When the posting has no requirements
heading, author the requirements from what the role owns and asks for, must or nice,
with keywords. `brief --validate`. Confirm the organization, role, slug, and what they
want (résumé, letter, or both) in one exchange (question `role`). A letter needs the
résumé's brief and map, not a rendered résumé.

## 2. Fit and gaps

`map`, then judge every classification yourself: **direct** (clearly met),
**transferable** (adjacent; say why in `note`), **gap** (no honest support; no evidence).
`map --validate`. `brief --coverage` lists requirement keywords the profile lacks
literally; sort them into synonyms of held evidence (reworded with the posting's term when
drafting, never added), qualifications worth confirming, and posting prose (ignored). Show
one screen: the counts, the must requirements that are gaps or transferable, and the
three groups. Ask one question (`gaps`): which of the second group do you genuinely have?
Each confirmed qualification goes through the `update` skill (statement, diff, explicit
yes, apply); then run `map` again.

## 3. The approach

Propose defaults, confirm in one exchange (question `approach`), write them to
`brief.json` under `approach`, and validate:

- `positioning`: the brief's recommendation and why. Executive leads with leadership,
  scope, and outcomes; builder with hands-on delivery. It changes emphasis and order,
  never a fact.
- `lead_evidence`: the three entities that lead, as ids with a label each.
- `compress`: roles, sections, or projects to shorten or leave out.
- `sections`: the manifest sections this résumé uses; default every section with
  evidence. A technical role keeps `skills`; an executive one may add `awards` or
  `interests` and drop `skills`.
- `resume_pages`: 2. One page only when the applicant expressly asks, never because a
  draft looks short.
- `letter_length`: `note` (150 to 200 words) or `page` (250 to 350); `note` when the
  posting asks for one.
- `tone`: the voice profile; conversational, warm first person for the letter.
- `avoid`: topics, phrases, or facts to keep out of both documents.

## 4. The alignment (when a letter is wanted)

`brief <brief.json> --alignment --flow apply --subject <slug>` lists what the brief has
not answered: why this role, which values and interests it engages, the focus it serves,
the letter's through-line, and the story that best supports it, with the identity
profile's own values, interests, and direction as options. Ask one at a time with a
suggested answer, record each, write them under `alignment`, and validate the brief. With
no identity profile, ask anyway and suggest `onboard` afterwards.

## 5. The résumé

1. `plan --kind resume` reads positioning, pages, and sections from the approach. Review
   the cut list; re-emphasize rather than inflate.
2. Rewrite each unit's `text` in the voice profile, every claim still traceable to its
   `source_ids`, nothing added from outside the profile. The template relies on:
   - the contact line staying on one line (abbreviate the state or drop a link);
   - a summary of two or three sentences the cited lead evidence supports, which may
     name the career focus from the identity profile;
   - a role line `Title — Organization, Location<tab>dates`, with any descriptor on the
     summary line beneath it, never in the role line (parsers read the whole line as
     title and company);
   - a project sub-head `Name — one-line descriptor` under its role;
   - skills as `Label<tab>skill, skill` lines, one per group, each citing every skill;
   - dated lines `Institution — Degree<tab>Year`, keeping the tab.
3. `render --kind resume --pdf`, then `check <document>`. A résumé must land exactly on
   its page target: too short, add relevant verified evidence or open the spacing; too
   long, cut. Look at the page renders under `.careerdocs/layout/`. Fix a failure at its
   source, never by weakening a check.
4. Record the path (question `resume`) and `commit --role-slug <slug> -m "feat(<slug>):
   tailored résumé"`.

## 6. The letter

1. `plan --kind cover_letter` carries the identity and alignment and picks the
   highest-value evidence for the page budget.
2. Draft one idea, the through-line, as a short story told to a future colleague: each
   paragraph opens on the last thought of the one before it, never in the posting's
   order. The résumé holds the facts, so imply qualifications through one or two examples
   chosen for the idea; a detail earns its place only when this role needs it. Name a gap
   the reader will notice once and turn it toward what they bring; never apologize.
   Enthusiasm needs an object: what they would be glad to help build, and why here. Let
   the evidence carry the confidence; no slogans, no "perfect fit". Qualifications trace
   to entities, employer facts to the posting, motives to the alignment. The greeting is
   the first body unit, cited to the contact entity; the template supplies the role line,
   the date, and the sign-off. Read it aloud and cut any sentence another applicant could
   have written.
3. `render --kind cover_letter --pdf`, then `check` (it also fails on any résumé bullet
   reproduced verbatim). Record the path (question `letter`) and
   `commit --role-slug <slug> -m "feat(<slug>): cover letter"`.

## 7. The report

One screen: what the plan cut for space, the honest gaps, the qualifications confirmed
and added, and the document paths. A revision is its own round: revise, render, check,
commit (`fix(<slug>): ...`).

## Guardrails

- Nothing enters the profile outside diff-then-approve; a synonym is reworded, not added.
- The approach and the alignment change emphasis, order, length, tone, and motive, never
  a fact. Gaps stay gaps.
- A document is done only when its record shows every check passed or skipped with a
  reason.
