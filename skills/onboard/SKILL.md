---
name: onboard
description: Onboard an applicant's existing career materials into one authoritative profile. Use when the applicant wants to import resumes, LinkedIn/network exports, and notes and reconcile them into a single careerdocs profile rather than scattered copies. The flow inventories the sources, runs profile import, has the agent extract candidates into candidates.json against the schema, builds a ProfileDiff, asks only the material questions the CLI generates (conflicts, missing dates, undecided visibility), records approval only after an explicit applicant yes, applies the diff, and refreshes the derived export. Resumable — an interrupted run continues from its workflow state without re-asking answered questions.
license: MIT
compatibility: "Python 3.10+; uv recommended. Requires the careerdocs core skill and its careerdocs CLI."
metadata:
  version: "0.1.0"
  author: "careerdocs-plugin contributors"
---

# onboard

Reconcile an applicant's existing career materials into **one** authoritative profile.
Read the core `careerdocs` skill first for the conventions this flow obeys
(the four authorities, the diff-then-approve rule, visibility, where state lives).

## When to use

The applicant has resumes, a LinkedIn or network export, and/or notes, and wants a single
authoritative profile instead of competing copies. This is the first flow to run for a new
workspace.

## The flow

Run these in order; the deterministic steps are `careerdocs` commands, the judgement steps
happen between them. Full detail in `references/playbook.md`.

1. **Confirm the workspace** — `doctor` shows which folder resolved and how. If it is
   the bare current directory (no workspace configured), ask the applicant which folder
   should hold their profile and run `config workspace <dir>`; in Cowork, the folder
   attached to the session is the workspace, so run `config init` there and pass it as
   `--workspace` instead of asking. Onboarding never lands in an arbitrary folder.
2. **Inventory the sources** the applicant points you at (resumes, exports, notes).
3. **`profile import <source>...`** — registers each source with its sha256 and emits text
   blocks (and, for a structured export, draft candidates).
4. **Extract candidates** — read the emitted text blocks and write `candidates.json` (each
   candidate typed, with provenance and a `ref`; achievements carry `parent_ref`). Do not
   invent facts; every candidate traces to a source.
5. **`profile diff candidates.json --flow onboard --subject <name>`** — merges candidates
   (dedup, precedence, conflicts) into a ProfileDiff and generates the material questions.
6. **Ask only the generated questions** — surface each to the applicant; record answers
   with `state answer onboard <subject> --question <id> --answer <text>`. Never ask a
   question the CLI did not generate; never re-ask an answered one.
7. **Turn answers into resolution operations** and re-diff, so the proposed profile
   reflects the applicant's choices.
8. **`profile approve <diff_id>`** — only after an explicit applicant "yes" to the rendered
   diff.
9. **`profile apply <diff_id>`** — writes the authoritative profile atomically and refreshes
   the derived export.
10. **`profile export`** — confirm the derived copy is present and labeled `derived: true`.

## Resuming

If interrupted, run `state resume onboard <subject>` to see the pending diff and any open
questions, and continue from there. Answered questions are never asked again.

## Guardrails

- No invented qualifications: a candidate with no source is not written.
- One authoritative profile: never hand-edit provider files; every change is a diff.
- Private facts stay private: they are in the profile but never in the export.
