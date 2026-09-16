---
name: cover-letter
description: Write a conversational, enthusiastic cover letter that connects the applicant's evidence to the employer's needs. Use after a tailored résumé exists for the role. Reuses the brief and map, drafts and reviews in the applicant's voice, and renders a complementary letter within the page budget.
license: MIT
compatibility: "Python 3.10+; uv recommended. Requires the careerdocs core skill, an onboarded profile, and an existing brief and map for the role (from the resume skill)."
metadata:
  version: "0.3.3"
  author: "careerdocs-plugin contributors"
---

# cover-letter

Write a cover letter that complements the résumé for the same role — never a prose
restatement of it. Read the core `careerdocs` skill first, and generate the résumé
(`resume`) before this so the brief and map already exist.

## When to use

A résumé for the role has been generated, so `applications/<slug>/brief.json` and
`map.json` exist. The applicant wants a one-page letter that adds context and motivation.

## The flow

Full detail in `references/playbook.md`.

1. **Reuse brief and map** — do not re-run `brief` or `map`, and do not re-ask questions
   already answered for the résumé. Read the existing artifacts.
2. **`plan --kind cover_letter --positioning <mode>`** — selects the highest-value
   evidence (must requirements with direct evidence first) into a few paragraph units
   within the one-page budget.
3. **Draft and review** — follow the playbook's writing guidance and editorial review
   before rendering.
4. **`render --kind cover_letter [--pdf]`** — fill the letter template.
5. **`check <document>`** — run the standard checks and separately confirm that no résumé
   bullet appears verbatim.
