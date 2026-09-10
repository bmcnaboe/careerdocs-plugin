# The careerdocs tutorial

What the onboard skill teaches the applicant, on every run. Deliver it in conversation,
adapted to their state and environment, in your own words and at their pace: never paste
this file, never skip it because the profile already exists. The applicant runs onboard
as much to learn how the plugin works as to import files.

## 1. What careerdocs is, in thirty seconds

One authoritative profile of the applicant's real qualifications, built from their own
documents with a source behind every fact. From it, résumés and cover letters tailored to a
specific job, drafted in the applicant's own voice, rendered into their own template, and
checked before they are called done. Four things are kept separate and never merged into
one blob: the **profile** (facts), the **voice** (how they write), the **templates** (how
documents look), and the **target role** (one job at a time). Nothing changes in the
profile without a diff they approve, and nothing about them leaves the machine.

## 2. Getting materials in

Say which of these the applicant has, and how to get the ones they do not:

- **Résumés**, current and older, DOCX or PDF. Older versions carry roles and details the
  current one dropped, so they are worth including.
- **The LinkedIn data export**: a set of CSV files LinkedIn generates, not the profile
  page. Steps: on LinkedIn open **Settings & Privacy → Data privacy → Get a copy of your
  data**; choose **Want something in particular?** and tick **Positions**, **Education**,
  **Skills**, and **Certifications** (or request the full archive); LinkedIn emails a
  download link, usually within ten minutes; unzip and put the CSVs in the workspace,
  `sources/` is the convention. `Positions.csv` becomes experience entries with exact
  start and end dates; the other files are read as text and mined for facts.
- **Why not a URL**: the profile page sits behind a login and LinkedIn's terms forbid
  fetching it, so neither the plugin nor an agent can use it. The nearest shortcut is the
  **More → Save to PDF** option on the applicant's own profile, which imports like a
  résumé.
- **Notes and records**: performance reviews, brag documents, project write-ups, a bio,
  anything that states a fact about their work, as Markdown or text.
- **Writing samples**: cover letters, emails, or posts they wrote and like. Not imported
  as facts; used to draft the voice profile.

Then how importing works: each file is registered with a checksum (so re-importing the
same file is a no-op), facts are extracted as candidates that each point back to a
source excerpt, candidates are merged with the profile, disagreements between sources
become questions, and the result is shown as a diff that is applied only after a yes.

## 3. Using the plugin, flow by flow

Give the invocation for the environment they are in:

| Flow | Claude Code and Cowork | Codex | In plain words |
| --- | --- | --- | --- |
| Set up, import, learn | `/careerdocs:onboard` | `$onboard` | "onboard my career documents" |
| Tailor a résumé | `/careerdocs:resume` | `$resume` | "tailor my résumé to this job description: …" |
| Matching cover letter | `/careerdocs:cover-letter` | `$cover-letter` | "write the cover letter for that role" |
| Record a change | `/careerdocs:update` | `$update` | "I just shipped X, add it to my profile" |

In Cowork, a session must have the workspace folder attached; in Claude Code and Codex
any folder works because the workspace is recorded.

**Résumé.** Have the job description at hand: pasted text, a file, or a URL they can open
and paste from. The flow builds a *role brief* (what the job really asks for), maps every
requirement to evidence in the profile as direct, transferable, or a gap, asks one
question, positioning (**executive**, leadership and scope first, or **builder**,
hands-on delivery first), plans the content within the template's page budget, drafts each
line in their voice, renders the DOCX (and PDF when LibreOffice is present), and runs
the five output checks: every line, number, and date traces to the profile; dates and
links are sane; and, when there is a PDF, its text extracts, it fits the template's page
budget, and the layout stays inside the margins. Gaps are never claimed and private facts
never render, by construction rather than by check. It ends by naming what was cut for
space and which requirements are honest gaps. Output lands in `applications/<role-slug>/`.

**Cover letter.** Runs after a résumé for the same role and reuses its brief and map.
Leads with the strongest evidence, complements the résumé instead of repeating it, and is
checked so no résumé line is copied verbatim. Same folder.

**Update.** For a new job, a new achievement, a certification, or a correction. The
applicant states it; the flow records it with them as the source, proposes a diff, applies
it after a yes, and reports which earlier documents are now stale.

**Doctor.** "Run careerdocs doctor" shows the workspace, config, profile size, templates,
voice, PDF converter, and dependencies at any time.

## 4. Where things live in the workspace

| Path | What it holds |
| --- | --- |
| `careerdocs.json` | Locations and policy only; no facts, no credentials |
| `profile/` | The authoritative profile, one Markdown file per entity |
| `sources.jsonl`, `approvals.jsonl`, `diffs/` | The ledgers: every source, every approval, every proposed change |
| `sources/` | The applicant's own files, by convention |
| `templates/resume/`, `templates/cover-letter/` | DOCX plus `template.json` per kind |
| `voice/voice.md` | The voice profile |
| `applications/<role-slug>/` | Brief, map, plan, and rendered documents per role |
| `baselines/` | Untargeted documents |
| `.careerdocs/state/` | Resumable workflow state |

## 5. Privacy and control

Every entity has a visibility: **public** renders anywhere, **restricted** renders only
into a document the applicant approved for it, **private** stays in the profile and never
appears in any document or export. Unverified facts never render. Nothing is sent
anywhere by the plugin; the agent runs on the machine or in the sandbox the applicant
chose. Editing profile files by hand works but bypasses the ledger, so prefer the update
flow.

## 6. Common situations

- **"I have a job description now."** Run the résumé flow; onboard is done.
- **"I changed jobs" or "I got a certification."** Run update.
- **"Something in my profile is wrong."** Run update and state the correction; it
  becomes a reviewed diff with the applicant as the source.
- **"The posting uses words my profile doesn't."** Name skills the way postings do —
  the literal tool, method, and model names — when confirming candidates, and the
  résumé flow's keyword coverage will ask about any requirement keyword the profile
  still lacks; only a skill you confirm is added.
- **"I want a different résumé design."** Restyle `templates/resume/template.docx`
  freely as long as the placeholders stay; `docs/templates-and-voice.md` in the plugin
  explains the placeholder loop, and the sanitized examples under `examples/applicant/`
  are a starting point.
- **"I want to start over."** Delete `profile/`, the ledgers, and `diffs/` in the
  workspace and run onboard again; the sources stay.
- **"Which files were used?"** `sources.jsonl` lists every registered source with its
  checksum and date.
