---
name: career-resume
description: Generate a tailored résumé for a specific job description from the applicant's authoritative profile. Use when the applicant has an onboarded profile and a target role, and wants a résumé mapped to that role's requirements. The flow builds a role brief from the job description, has the agent complete it, maps each requirement to direct/transferable/gap evidence, chooses a positioning (executive or builder), plans content within the template's page budget, drafts units in the applicant's voice, renders into the template, runs the five output checks, and reports cuts and gaps. It never invents qualifications — a gap requirement is named honestly and never claimed.
license: MIT
compatibility: "Python 3.11+; uv recommended. Requires the careerdocs core skill and an onboarded profile. Optional LibreOffice for PDF checks."
metadata:
  version: "0.1.0"
  author: "careerdocs-plugin contributors"
---

# career-resume

Turn a job description into a tailored résumé grounded entirely in the applicant's
authoritative profile. Read the core `careerdocs` skill first.

## When to use

The profile is onboarded (via `career-onboard`) and the applicant has a specific role in
mind. Produces a role brief, a requirement-to-evidence map, a content plan, a rendered
résumé, and an output record — in that order, saved under the application folder.

## The flow

Full detail in `references/playbook.md`.

1. **`brief <jd-file>`** — build the role brief skeleton (requirements with must/nice,
   keywords, a positioning recommendation). Complete the organization, role, and any
   nuance; validate with `brief --validate`.
2. **`map`** — for each requirement, the CLI proposes evidence and a classification. Apply
   real judgement: **direct** (the profile clearly meets it), **transferable** (adjacent
   experience), or **gap** (no honest support). A gap carries no evidence.
3. **Choose positioning** — executive or builder (default from config). This changes
   selection and emphasis, never the facts.
4. **`plan --positioning <mode>`** — select, order, and emphasize evidence within the
   template's page budget; anything over budget is cut and reported.
5. **Draft units in voice** — rewrite each unit's text in the applicant's voice
   (`voice.md`), keeping every claim traceable to its `source_ids`.
6. **`render --kind resume [--pdf]`** — fill the template; a timestamped file is written,
   never overwriting.
7. **`check <document>`** — run the five checks (factual, links/dates, extraction,
   pagination, layout) and write the output record.
8. **Report cuts and gaps** — tell the applicant what was cut for space and which
   requirements are gaps, so they decide how to proceed.

## Guardrails

- No invented qualifications: the factual check rejects any number or line that does not
  trace to a cited entity; a gap requirement is never claimed.
- Positioning changes emphasis and order only; switching it must not change a fact.
- A document is "done" only when its record shows every check passed (or skipped with a
  reason, e.g. the PDF checks offline).
