---
name: cover-letter
description: Write a cover letter with a through-line of the applicant's own. It connects their identity (values, motivations, career focus, stories) and the role alignment to the employer's needs in a conversational, enthusiastic first person. Use after a tailored résumé exists for the role. Reuses the brief and map, settles the alignment if apply has not, drafts and reviews in the applicant's voice, and renders a complementary letter within the page budget.
license: MIT
compatibility: "Python 3.10+; uv recommended. Requires the careerdocs core skill, an onboarded profile, and an existing brief and map for the role (from the resume skill)."
metadata:
  version: "0.4.3"
  author: "careerdocs-plugin contributors"
---

# cover-letter

A letter that could only have been written by this applicant for this role. Read the
core `careerdocs` skill first. The letter draws on three authorities at once: the profile
for every fact, the voice for how it sounds, and the identity, with the brief's role
alignment, for why it is being written and what holds it together.

## When to use

A résumé exists for the role (so `brief.json` and `map.json` exist) and the applicant
wants the matching letter. The apply skill invokes this flow after the résumé; on its own
it asks only what apply would have asked and has not.

## The flow

Full detail in `references/playbook.md`.

1. **Reuse the brief, map, identity, and alignment** — read them; re-run nothing and
   re-ask nothing the workflow state already answers. If the brief has no `alignment`,
   settle it now with `brief --alignment`, one question at a time, written to the brief.
2. **`plan --kind cover_letter --positioning <mode>`** — selects the highest-value
   evidence into a few paragraph units within the page budget and carries the identity
   path and the alignment into the plan.
3. **Draft and review** — write a short, personal note about why this work matters to
   the applicant and how they would help. Choose a few relevant facts and, when it fits,
   a human detail that shows how they work. Let the role guide what belongs; follow the
   applicant's natural train of thought rather than the posting's order. Read it aloud.
4. **`render --kind cover_letter [--pdf]`** — fill the letter template.
5. **`check <document>`** — run the standard checks and separately confirm that no résumé
   bullet appears verbatim.

## Guardrails

- The identity and alignment supply motive, emphasis, and tone; every fact still traces
  to a profile entity, and a gap requirement is never claimed.
- A letter that walks the requirements list or repeats the résumé is not done. If it
  could have been written by anyone with the same résumé, revise until it could not.
