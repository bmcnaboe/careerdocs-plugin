---
name: cover-letter
description: Generate a cover letter that complements a tailored résumé for the same role. Use after a résumé has been generated for a role (via the resume skill), when the applicant wants a matching cover letter. The flow reuses the existing role brief and requirement map without re-asking anything, plans a short letter that leads with the highest-value evidence, drafts it in the applicant's voice, renders into the letter template, and runs the checks — including one that no résumé bullet is reproduced verbatim. It complements rather than repeats the résumé, traces every claim to a profile ID, never claims a gap requirement, and fits the letter's page budget.
license: MIT
compatibility: "Python 3.10+; uv recommended. Requires the careerdocs core skill, an onboarded profile, and an existing brief and map for the role (from the resume skill)."
metadata:
  version: "0.1.0"
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
3. **Draft in voice** — write the letter in the applicant's voice as connected prose that
   *complements* the résumé: motivation, fit, and context, not a re-listing of bullets.
4. **`render --kind cover_letter [--pdf]`** — fill the letter template.
5. **`check <document>`** — run the checks. Additionally confirm no résumé bullet appears
   verbatim, every claim traces to a profile ID, and no gap requirement is claimed.

## Guardrails

- Complement, do not repeat: the verbatim-bullet check fails if a résumé bullet is
  reproduced word-for-word.
- Honest about gaps: a gap requirement is never claimed; if it matters, address it as
  growth or omit it — never invent coverage.
- Every claim traces to a profile entity, like the résumé.
- The letter fits its page budget (one page by default).
