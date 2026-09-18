---
name: onboard
description: Guided setup and first-run tutorial for careerdocs, and the flow that reconciles an applicant's existing career materials into one authoritative profile. Use when the applicant runs the onboard skill, asks to set up or get started with careerdocs, or wants to import résumés, a LinkedIn data export, and notes into a single profile rather than scattered copies. Idempotent, so it first checks what already exists (workspace, profile, sources, templates, voice, identity, pending state) and walks through only what is missing. It explains how to obtain each material (including the LinkedIn data export), runs profile import, extracts candidates, builds a ProfileDiff, asks only the questions the CLI generates, records approval only after an explicit yes, applies the diff, sets up templates and voice, captures the applicant's identity by interview (values, personality, motivations, working style, career focus, interests), and ends with a short tour of the other flows. Resumable without re-asking answered questions.
license: MIT
compatibility: "Python 3.10+; uv recommended. Requires the careerdocs core skill and its careerdocs CLI."
metadata:
  version: "0.5.0"
  author: "careerdocs-plugin contributors"
---

# onboard

The front door of careerdocs: part setup, part tutorial, and the flow that turns an
applicant's scattered materials into **one** authoritative profile. Read the core
`careerdocs` skill first for the conventions this flow obeys (the five authorities, the
diff-then-approve rule, visibility, where state lives). Command detail is in
`references/playbook.md`.

The whole run is a conversation. Ask one thing at a time, explain why it is needed in a
sentence, and accept "skip" or "later" for anything optional. Never make the applicant
read this file.

**This skill teaches, whatever the state.** Every run ends with the applicant knowing
what exists, how to get more material in (the LinkedIn export steps included), and how
to run the other flows. That content is `references/tutorial.md`; deliver it in your own
words, adapted to their state and environment, without waiting to be asked. A status
line followed by "give me paths" is not an acceptable outcome.

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
- **Profile already has entities**: onboarding was done before. Say so and summarize
  what the profile holds (roles, date range, counts, templates and voice present or
  not). Then give the returning-applicant briefing before asking for anything: how the
  plugin is used from here (tutorial section 3), how to get more material in, the
  LinkedIn export steps included (section 2), and where things live (section 4). Close
  by offering, not requiring, the next moves: add new sources (Stage 2 for those files
  only), record a single new fact (the `update` skill), set up whatever Stage 4 finds
  missing, revisit their identity profile (career focus and interests change; values
  rarely do), or run the résumé flow if they have a job description at hand.
- **Pending onboard state** (`state resume onboard <subject>` lists a diff or open
  questions): resume there; answered questions are never asked again.
- **Sources already registered** (the provider's `sources.jsonl`): list them; do not
  re-import a file whose sha256 is already recorded.
- **Templates, voice, or identity missing** (`doctor` reports each): note it now; Stage 4
  handles them after the profile exists, so the applicant sees value before doing setup
  chores.
- **No git repository** (`doctor` shows `history: archive`): explain in a sentence that a
  git repository in the workspace keeps every generation and revision round as a commit
  instead of an archive folder, and offer to run `git init` there (never a remote, never a
  push). The applicant decides; the archive works without it.
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
2. **Extract candidates** into `candidates.json`: every candidate typed — contact,
   experience (with `kind` `advising`, `board`, or `volunteer` when it is not
   employment), achievement, education, skill (with a `category` when the résumé groups
   them), project, credential, patent, publication, award, interest, affiliation — with
   provenance naming its `source_id` and an excerpt; experiences carry a `ref`,
   achievements a `parent_ref`. Never invent a fact. When two sources disagree, include
   both; the merge records the disagreement as a conflict.
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

## Stage 4 — Templates, voice, and identity

All three are applicant-owned files in the workspace; the résumé and cover-letter flows
need them. Handle whichever `doctor` reported missing.

- **Templates**: a DOCX with Jinja placeholders plus a `template.json` manifest per
  kind, under `templates/resume/` and `templates/cover-letter/`. If the applicant has
  none, offer to copy the plugin's default design from `examples/applicant/templates/`
  (next to `skills/` in the plugin): a single-column résumé whose manifest offers every
  common section (Summary, Experience with projects folded under their roles, Projects,
  Education, Certifications, Patents, Publications, Awards, Affiliations, Volunteer
  Experience, Technical Focus, Interests), each optional and picked per role, and a
  matching letter with the role line and date. Say they can restyle the DOCX freely as
  long as the placeholders stay. If they have a favourite résumé layout, explain the
  placeholder loop from `docs/templates-and-voice.md` and offer to convert it.
- **Voice**: `voice/voice.md`, a frontmatter block with `person`, `tense_rules`, `tone`,
  `preferred_terms`, `banned_phrases`, `sentence_shape`, and `sample_sentences`. Draft it
  from the writing samples gathered in Stage 1 and from how the applicant answered
  questions; if there are no samples, propose a plain, concrete default and ask three
  short questions (first or third person, words they never want to see, two sentences
  they are proud of). Show the draft and write it only after a yes.
- **Identity**: `identity/identity.md`, who the applicant is beyond the facts, so a cover
  letter has a through-line of their own instead of a walk through the requirements.
  Run `identity questions --flow onboard --subject <name>`; it lists one question per
  section still missing (values, personality, motivations, working style, career focus,
  interests) with a stable id, and marks the ones already answered. Ask them one at a
  time, in plain language, with why each matters in a sentence; record each answer with
  `state answer`. Listen for the stories they tell while answering and keep them for
  the file's body. Draft the file from the answers, in their words, never inventing a
  value or a story; show it; write it only after a yes. The durable sections change
  rarely; career focus and interests are worth revisiting when they return.

In a git workspace, close the stage by committing the setup:
`careerdocs commit -m "feat: onboard the profile" --path careerdocs.json --path templates --path voice --path identity --path sources`
(the profile is always included; the command is a no-op without a repository).

## Stage 5 — The tutorial

End every run, first or returning, with the tutorial in `references/tutorial.md`:
what careerdocs is, how to get materials in (LinkedIn export steps and the profile-PDF
alternative), how each flow is invoked in this environment and what it needs at hand,
where things live in the workspace, privacy, and the common situations. Adapt it: a
first-run applicant gets the whole arc; a returning one gets the parts that match what
they have and what is missing. Then offer to run the apply flow right away if they have
a job description at hand.

## Guardrails

- No invented qualifications: a candidate with no source is not written.
- One authoritative profile: never hand-edit provider files; every change is a diff.
- Private facts stay private: they are in the profile but never in the export.
- Idempotent: check before doing; never re-import, re-ask, or overwrite without a yes.
- Identity is the applicant's own account: drafted from their answers, never inferred
  from the profile or invented, and never a source of qualifications.
