---
name: resume
description: Generate a tailored résumé for a specific job description from the applicant's authoritative profile. Use when the applicant has an onboarded profile and a target role, and wants a résumé mapped to that role's requirements. The flow builds a role brief from the job description, has the agent complete it, maps each requirement to direct/transferable/gap evidence, chooses a positioning (executive or builder), plans content within the template's page budget, drafts units in the applicant's voice, renders into the template, runs the five output checks, and reports cuts and gaps. It never invents qualifications — a gap requirement is named honestly and never claimed.
license: MIT
compatibility: "Python 3.10+; uv recommended. Requires the careerdocs core skill and an onboarded profile. Optional LibreOffice for PDF checks."
metadata:
  version: "0.5.0"
  author: "careerdocs-plugin contributors"
---

# resume

Turn a job description into a tailored résumé grounded entirely in the applicant's
authoritative profile. Read the core `careerdocs` skill first.

## When to use

The profile is onboarded (via `onboard`) and the applicant has a specific role in
mind. Produces a role brief, a requirement-to-evidence map, a content plan, a rendered
résumé, and an output record — in that order, saved under the application folder.

## The flow

Full detail in `references/playbook.md`.

1. **`brief <jd-file>`** — build the role brief skeleton (requirements with must/nice,
   keywords, a positioning recommendation). Complete the organization, role, and any
   nuance; validate with `brief --validate`.
2. **`map`** — for each requirement, the CLI proposes evidence and a classification. Apply
   real judgement: **direct** (the profile clearly meets it), **transferable** (adjacent
   experience), or **gap** (no honest support). A gap carries no evidence. Then
   `brief --coverage` lists requirement keywords the profile lacks: reword a synonym with
   the posting's term; add a genuinely held skill only through the update flow with the
   applicant's yes; leave the rest.
3. **Choose positioning** — executive or builder (default from config). This changes
   selection and emphasis, never the facts.
4. **`plan --positioning <mode>`** — target two pages by default, selecting, ordering,
   and emphasizing evidence accordingly. Use one page only when the applicant expressly
   requests it. The template's sections are all available; the approach's `sections`
   (or `--sections`) picks the ones this role uses — a Technical Focus for a technical
   role, Awards or Interests for an executive one — and a one-page résumé is the same
   design with fewer sections and units. Anything over the target is cut and reported.
5. **Draft units in voice** — rewrite each unit's text in the applicant's voice
   (`voice.md`), keeping every claim traceable to its `source_ids`: the summary from its
   cited lead evidence, skills as labeled lines, each role and project sub-head in the
   conventions the playbook gives.
6. **`render --kind resume [--pdf]`** — fill the template; the document is written as
   `<Name>-<Org>-<Role>-Resume.docx`. In a git workspace an uncommitted previous render
   is committed first; otherwise it moves to `outputs/archive/`.
7. **`check <document>`** — run the five checks (factual, links/dates, extraction,
   pagination, layout) and write the output record. A résumé must reach its page target;
   revise the content or layout and rerender when it comes up short.
8. **`commit --role-slug <slug> -m "<message>"`** — end the round. In a git workspace
   this commits the application folder and its state under a Conventional Commit
   message; elsewhere it is a no-op and the archive holds the history. Repeat after
   every revision round.
9. **Report cuts and gaps** — tell the applicant what was cut for space and which
   requirements are gaps, so they decide how to proceed.

## Guardrails

- No invented qualifications: the factual check rejects any number or line that does not
  trace to a cited entity; a gap requirement is never claimed.
- Positioning changes emphasis and order only; switching it must not change a fact.
- A document is "done" only when its record shows every check passed (or skipped with a
  reason, e.g. the PDF checks offline).
