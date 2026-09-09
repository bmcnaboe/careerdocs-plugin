---
name: onboard
description: Guided setup and first-run tutorial for careerdocs, and the flow that reconciles an applicant's existing career materials into one authoritative profile. Use when the applicant runs the onboard skill, asks to set up or get started with careerdocs, or wants to import résumés, a LinkedIn data export, and notes into a single profile rather than scattered copies. Idempotent, so it first checks what already exists (workspace, profile, sources, templates, voice, pending state) and walks through only what is missing. It explains how to obtain each material (including the LinkedIn data export and the profile-PDF alternative), runs profile import, extracts candidates, builds a ProfileDiff, asks only the questions the CLI generates, records approval only after an explicit yes, applies the diff, sets up templates and voice, and ends with a short tour of the other flows. Resumable without re-asking answered questions.
license: MIT
compatibility: "Python 3.10+; uv recommended. Requires the careerdocs core skill and its careerdocs CLI."
metadata:
  version: "0.2.0"
  author: "careerdocs-plugin contributors"
---

# onboard

The front door of careerdocs: part setup, part tutorial, and the flow that turns an
applicant's scattered materials into **one** authoritative profile. Read the core
`careerdocs` skill first for the conventions this flow obeys (the four authorities, the
diff-then-approve rule, visibility, where state lives). Command detail is in
`references/playbook.md`.

The whole run is a conversation. Ask one thing at a time, explain why it is needed in a
sentence, and accept "skip" or "later" for anything optional. Never make the applicant
read this file.

## Stage 0 — Check what is already there

Run first, every time; it makes the skill idempotent.

```sh
careerdocs doctor --json
```

Read the report and branch on it:

- **Workspace unresolved** (`workspace_source` is `cwd`): explain that the workspace is
  the one folder that holds the profile, templates, voice, and generated documents, ask
  which folder should be it (the installer suggests `~/career-workspace`), and run
  `config workspace <dir>`. In Cowork, the folder attached to the session is the
  workspace: run `config init --workspace <that folder>` if it lacks `careerdocs.json`,
  pass `--workspace <that folder>` on every command, and do not ask.
- **Profile already has entities**: onboarding was done before. Say so, summarize what
  the profile holds (roles, date range, counts), and offer three exits: add new sources
  (continue with Stage 2 for those sources only), record a single new fact (hand off to
  the `update` skill), or just the tour (skip to Stage 5).
- **Pending onboard state** (`state resume onboard <subject>` lists a diff or open
  questions): resume there; answered questions are never asked again.
- **Sources already registered** (the provider's `sources.jsonl`): list them; do not
  re-import a file whose sha256 is already recorded.
- **Templates or voice missing**: note it now; Stage 4 handles it after the profile
  exists, so the applicant sees value before doing setup chores.
- **Dependencies missing or the CLI failing**: stop and fix that first; nothing below
  works without the CLI.

## Stage 1 — Gather the materials

Ask what the applicant has, in this order, and where each file lives. Everything is
optional except at least one résumé or export; the flow works with a single résumé.

1. **Résumés**, current and older, DOCX or PDF. Older versions matter: they carry roles
   and details the current one dropped.
2. **LinkedIn data export**. This is a set of CSV files LinkedIn generates, not the
   profile page. If the applicant does not have it, give these steps: on LinkedIn open
   **Settings & Privacy → Data privacy → Get a copy of your data**, choose
   **Want something in particular?** and tick **Positions**, **Education**, **Skills**,
   and **Certifications** (or request the full archive), then download the zip from the
   email that arrives in about ten minutes and put the CSVs in the workspace, `sources/`
   works well. `Positions.csv` becomes experience candidates with exact dates; the other
   files are read as text. A profile URL cannot be used: the page sits behind a login
   and LinkedIn's terms forbid fetching it. The nearest shortcut is the **Save to PDF**
   option on the applicant's own profile, which imports like any résumé.
3. **Notes and other records**: performance reviews, brag documents, project write-ups,
   a bio, Markdown or text. Anything that states a fact about the applicant's work.
4. **Writing samples** for the voice profile: cover letters, emails, posts the applicant
   wrote and likes. Used in Stage 4, so ask now and set aside.

Confirm the list back, with paths, before importing. If the applicant wants to gather
more first, stop here; the next run resumes at Stage 0 with nothing lost.

## Stage 2 — Build the profile

1. **`profile import <path>...`** registers each source with its sha256 and returns text
   blocks (and, for a CSV, draft candidates).
2. **Extract candidates** into `candidates.json`: every candidate typed, with provenance
   naming its `source_id` and an excerpt; experiences carry a `ref`, achievements a
   `parent_ref`. Never invent a fact. When two sources disagree, include both; the merge
   records the disagreement as a conflict.
3. **`profile diff candidates.json --flow onboard --subject <name>`** merges, applies
   precedence, and generates the material questions.
4. **Ask only the generated questions**, one at a time, in plain language, and record
   each with `state answer onboard <subject> --question <id> --answer <text>`. Never ask
   a question the CLI did not generate; never re-ask an answered one.
5. **Resolve and re-diff**, then show the rendered diff and explain it in a few lines:
   how many roles, which conflicts were resolved and how, what is marked private.
6. **`profile approve <diff_id>`** only after an explicit yes. **`profile apply`** writes
   the profile atomically and refreshes the derived export.

## Stage 3 — Confirm

Run `profile validate` and `doctor` again, and tell the applicant in one paragraph what
now exists and where: the profile folder, the source ledger with provenance for every
fact, and that private facts stay out of every export.

## Stage 4 — Templates and voice

Both are applicant-owned files in the workspace; the résumé and cover-letter flows need
them. Handle whichever `doctor` reported missing.

- **Templates**: a DOCX with Jinja placeholders plus a `template.json` manifest per
  kind, under `templates/resume/` and `templates/cover-letter/`. If the applicant has
  none, offer to copy the plugin's sanitized examples from `examples/applicant/templates/`
  (next to `skills/` in the plugin) as a starting point, and say they can restyle the
  DOCX freely as long as the placeholders stay. If they have a favourite résumé layout,
  explain the placeholder loop from `docs/templates-and-voice.md` and offer to convert it.
- **Voice**: `voice/voice.md`, a frontmatter block with `person`, `tense_rules`, `tone`,
  `preferred_terms`, `banned_phrases`, `sentence_shape`, and `sample_sentences`. Draft it
  from the writing samples gathered in Stage 1 and from how the applicant answered
  questions; if there are no samples, propose a plain, concrete default and ask three
  short questions (first or third person, words they never want to see, two sentences
  they are proud of). Show the draft and write it only after a yes.

## Stage 5 — The tour

End with a short, concrete tour, adapted to the environment the applicant is in:

- **What exists now**: one profile, every fact traceable to a source, changes only
  through reviewed diffs.
- **Per application**: `resume` builds a role brief from a job description, maps each
  requirement to evidence, drafts in their voice, renders into the template, and runs
  the checks; `cover-letter` reuses that brief for a complementary letter. Invoke as
  `/careerdocs:resume` and `/careerdocs:cover-letter` in Claude Code and Cowork,
  `$resume` and `$cover-letter` in Codex, or in plain words ("tailor my résumé to this
  job description").
- **When something changes**: `update` records a new achievement, role, or correction
  as a reviewed diff and reports which past documents it makes stale.
- **Where things land**: `applications/<role-slug>/` per role, `baselines/` for
  untargeted documents, and "run careerdocs doctor" whenever they want to see the state.
- **Privacy**: everything stays in the workspace on this machine; nothing about them is
  sent anywhere by this plugin.

Offer to run the résumé flow right away if they have a job description at hand.

## Guardrails

- No invented qualifications: a candidate with no source is not written.
- One authoritative profile: never hand-edit provider files; every change is a diff.
- Private facts stay private: they are in the profile but never in the export.
- Idempotent: check before doing; never re-import, re-ask, or overwrite without a yes.
