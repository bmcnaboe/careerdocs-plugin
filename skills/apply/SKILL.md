---
name: apply
description: Produce a complete application for one job posting through a short guided interview that orchestrates the update, resume, and cover-letter skills. Use when the applicant has an onboarded profile and a posting in hand and wants the whole thing done in one sitting — the role brief and requirement map, a fit summary with the keywords the profile lacks, profile updates for qualifications they confirm they hold, an agreed approach (positioning, lead evidence, what to compress, résumé length, letter length and tone, what to avoid), then the tailored résumé and the complementary cover letter with every check passed and the cuts and gaps reported. Every question carries a suggested answer so the fast path is a yes; nothing enters the profile without an explicit approval; a gap is never claimed. Resumable — an interrupted run continues from its recorded answers.
license: MIT
compatibility: "Python 3.10+; uv recommended. Requires the careerdocs core skill, an onboarded profile, templates, and voice; the update, resume, and cover-letter skills do the work. Optional LibreOffice for PDF checks."
metadata:
  version: "0.2.1"
  author: "careerdocs-plugin contributors"
---

# apply

One posting in, a checked résumé and cover letter out, through a short interview. This
skill owns the conversation and the decisions; the `update`, `resume`, and `cover-letter`
skills own the mechanics and are invoked, never restated. Read the core `careerdocs`
skill first.

## When to use

The profile is onboarded and the applicant has a specific posting. Use `resume` or
`cover-letter` on their own when only one document is wanted or the approach is already
settled.

## The interview

Full detail in `references/playbook.md`. Every question carries a suggested answer so the
fast path is a yes; never ask what the workflow state already answers.

1. **The role** — take the posting (pasted text, a file, or text pasted from a URL), save
   it under the application folder, run `brief`, and confirm the organization, role, and
   slug in one exchange.
2. **Fit and gaps** — run `map` with real judgement and `brief --coverage`, then show one
   screen: the direct, transferable, and gap requirements, and the requirement keywords
   the profile lacks, sorted into synonyms of existing evidence (reworded later, never
   added), qualifications worth confirming, and posting prose (ignored). Ask one
   question: which of these do you genuinely have? Each confirmed qualification goes
   through the `update` skill (statement, diff, explicit yes, apply); then `map` again.
3. **The approach** — propose and confirm in one pass: positioning with the reason, the
   three pieces of evidence that lead, what to compress or leave out, résumé length,
   letter length (a brief note or a full page) and tone, and anything to avoid. Record
   the agreed approach on the brief (`approach`), where `plan` and the drafting steps
   read it.
4. **The documents** — run the `resume` skill from its plan step, then the
   `cover-letter` skill, each honoring the approach. Both end with every check passed.
5. **The report** — what was cut for space, which requirements remain honest gaps, which
   qualifications were confirmed and added, and where the files are.

## Resuming

State lives under flow `apply`, subject `<role-slug>`. `state resume apply <slug>` shows
the step, any pending diff, and open questions; continue from there without re-asking.

## Guardrails

- Nothing enters the profile outside the diff-then-approve rule; a qualification the
  applicant has not confirmed is never added, and a synonym is reworded, not added.
- The approach changes emphasis, order, length, and tone; never a fact. Gaps stay gaps.
- Delegate, do not duplicate: the mechanics live in `update`, `resume`, and
  `cover-letter`; this skill decides and hands off.
