---
name: onboard
description: Set up careerdocs and build the applicant's one authoritative profile from their existing materials (résumés, a LinkedIn data export, notes), then teach them how the plugin works. Use when the applicant wants to set up, get started, onboard, import a résumé or LinkedIn export, or revisit their voice or identity profile. Idempotent and resumable, so it checks what exists and does only what is missing.
license: MIT
compatibility: "Python 3.10+; uv recommended. Requires the careerdocs core skill."
metadata:
  version: "0.6.0"
  author: "careerdocs-plugin contributors"
---

# onboard

Setup, import, and a short tutorial, as one conversation. Read the core `careerdocs`
skill first; commands and file shapes are in its `references/cli.md`. Ask one thing at a
time, say why in a sentence, accept "skip" or "later" for anything optional, and never
ask what the CLI or the workflow state already answers.

## 1. Check what exists

Run `doctor --json` and branch on it:

- **No workspace resolved**: the workspace is the one folder for the profile, templates,
  voice, and documents. Ask which folder (default `~/career-workspace`) and run
  `config workspace <dir>`. In Cowork use the attached folder without asking.
- **The profile already has entities**: say what it holds (roles, date range, counts,
  what is set up), give the tour (section 5), then offer: new sources, one new fact (the
  `update` skill), missing setup, a revisit of career focus and interests, or an
  application (the `apply` skill).
- **Pending onboard state** (`state resume onboard <subject>`): continue from it.
- **No git repository** (`history: archive`): offer `git init` in the workspace, never a
  remote or a push; it keeps every round as a commit. Ignore `.careerdocs/layout/`.
- **Dependencies missing**: fix that first.

## 2. Gather materials

At least one résumé; everything else is optional.

- **Résumés**, current and older, DOCX or PDF. Older ones carry roles the current one
  dropped.
- **The LinkedIn data export**: on LinkedIn, Settings & Privacy, Data privacy, Get a copy
  of your data; tick Positions, Education, Skills, and Certifications, or the full
  archive. The zip arrives by email in about ten minutes; unzip it into `sources/`. A
  profile URL cannot be used (login wall, terms of use). The nearest shortcut is Save to
  PDF on their own profile page, which imports like a résumé.
- **Notes**: reviews, brag documents, write-ups, a bio.
- **Writing samples** for the voice profile; not imported as facts.

Confirm the list with paths before importing. Never re-import a file whose sha256 is
already in `sources.jsonl`.

## 3. Build the profile

1. `profile import <path>...` registers each source and returns its text blocks (and
   draft candidates from a CSV).
2. Write `candidates.json` from the text. Type every candidate; an experience that is
   advising, a board seat, or volunteer work carries `kind`; a skill carries a
   `category`; name skills the way postings do (the literal tool, method, and model
   names). Each candidate cites its `source_id` with an `excerpt`. Never invent a fact.
   When sources disagree, include both; the merge records the conflict.
3. `profile diff candidates.json --flow onboard --subject <name>` merges, applies
   precedence (applicant statement, then verified import, then newest import), and
   generates the material questions. Ask only those, one at a time, in plain words, and
   record each with `state answer`. Turn the answers into `resolve_conflict`,
   `update_field`, and `set_visibility` operations and re-diff.
4. Show the summary in a few lines (roles, resolved conflicts, what is private). After
   an explicit yes: `profile approve`, `profile apply`, `profile validate`. Tell them in a
   paragraph what now exists and where.

## 4. Templates, voice, identity

Whatever `doctor` reports missing, once the profile exists:

- **Templates**: offer to copy the plugin's default design from
  `examples/applicant/templates/` (beside `skills/`) into `templates/resume/` and
  `templates/cover-letter/`. The DOCX can be restyled freely as long as the placeholders
  stay (`docs/templates-and-voice.md`).
- **Voice**, `voice/voice.md`: JSON frontmatter with `person`, `tense_rules`, `tone`,
  `preferred_terms`, `banned_phrases`, `sentence_shape`, `sample_sentences`, and a body
  for document-specific guidance. Draft it from the writing samples and how they
  answered; with no samples, ask three short questions (first or third person, words
  they never want to see, two sentences they are proud of). Write it after a yes.
- **Identity**, `identity/identity.md`: `identity questions --flow onboard --subject
  <name>` lists one question per missing section (values, personality, motivations,
  working style, career focus, interests). Ask them one at a time, saying why each
  matters; record each with `state answer`; keep the stories they tell for the body.
  Draft it in their words, never inferred from the profile, write it after a yes, and
  run `identity validate`. Values rarely change; career focus and interests are worth
  revisiting when they return.

Close with `commit -m "feat: onboard the profile" --path careerdocs.json --path templates
--path voice --path identity --path sources` (a no-op without git).

## 5. The tour

End every run, first or returning, by explaining in your own words, adapted to what they
have: one profile with a source behind every fact; nothing changes without a diff they
approve; nothing leaves their machine; how to get more material in; and the flows in this
environment. `apply` takes a posting and produces the résumé, the letter, or both;
`update` records a new fact or a correction; `onboard` again revisits focus and
interests; "run careerdocs doctor" shows the setup at any time. Then offer to start
`apply` if they have a posting at hand.

## Guardrails

- A candidate with no source is not written. Private facts never leave the profile.
- Check before doing: never re-import, re-ask, or overwrite without a yes.
- The identity is the applicant's own account, never inferred, never a source of facts.
