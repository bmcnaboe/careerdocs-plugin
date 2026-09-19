---
name: careerdocs
description: Shared conventions and the careerdocs CLI behind the onboard, update, and apply skills. Load it before running any careerdocs command. It covers the five authorities (qualifications, voice, identity, templates, target role), how to run the CLI and locate the workspace, the diff-then-approve rule for every profile change, visibility, and where every artifact lives.
license: MIT
user-invocable: false
compatibility: "Python 3.10+; uv recommended (uv run), python3 fallback. Offline. Optional LibreOffice (soffice) for PDF output and the PDF checks."
metadata:
  version: "0.6.0"
  author: "careerdocs-plugin contributors"
---

# careerdocs

The rules every flow obeys and the deterministic CLI they all call. The CLI does the
mechanical work (parsing, merging, planning, rendering, checking); judgement happens
between commands, in the conversation. Command and file detail: `references/cli.md`.

## Five authorities, kept separate

1. **Qualifications**: the profile, typed entities with stable ids, provenance,
   verification, and visibility, stored as structured Markdown under `profile/`.
2. **Voice**: how the applicant writes, `voice/voice.md`.
3. **Identity**: who they are beyond the facts (values, personality, motivations,
   working style, career focus, interests, stories), `identity/identity.md`. Never a
   source of qualifications.
4. **Templates**: a DOCX plus a `template.json` manifest per kind, under `templates/`.
5. **Target role**: the brief for one application, under `applications/<slug>/`.

`careerdocs.json` only locates these. It never holds qualifications or credentials.

## Running the CLI

```sh
uv run <plugin>/skills/careerdocs/scripts/careerdocs.py <command> [--workspace <dir>] [--json]
```

`python3` works without uv. `--json` gives machine output; diagnostics go to stderr; exit
0 ok, 1 a check failed, 2 usage or contract error.

The **workspace** is the one folder holding everything above. It resolves from
`--workspace`, then `CAREERDOCS_WORKSPACE`, then the nearest `careerdocs.json` at or
above the current directory, then the default recorded in `~/.config/careerdocs/workspace`.
A bare folder is refused (`WORKSPACE_UNRESOLVED`); never make one implicitly. When
nothing resolves, ask which folder it should be and run `config workspace <dir>`. In
Cowork the folder attached to the session is the workspace: pass it as `--workspace` on
every command and run `config init` there if it lacks `careerdocs.json`. `doctor` shows
what resolved and how.

## Diff, then approve

Every profile change is a proposal. `profile diff` builds a diff and mutates nothing;
show its summary and get an explicit yes; `profile approve`; `profile apply`, which
refuses if the profile changed underneath. Never approve without a real yes. Never edit
`profile/` by hand.

## Honesty

Every line of a document traces to a cited entity; the factual check rejects anything
that does not. A gap requirement is named, never claimed. `private` entities never
render; `restricted` ones render only into a document approved for them; `unverified`
facts never render; an unresolved conflict blocks its field.

## Where things live

| Path | Holds |
| --- | --- |
| `profile/` | the profile, with `sources.jsonl`, `approvals.jsonl`, `diffs/` |
| `voice/voice.md`, `identity/identity.md` | voice and identity |
| `templates/resume/`, `templates/cover-letter/` | DOCX plus manifest |
| `applications/<slug>/` | `job-description.md`, `brief.json`, `map.json`, `plan.<kind>.json`, the documents and their `.record.json` |
| `baselines/<positioning>/` | role-less résumés |
| `.careerdocs/state/<flow>/<subject>.json` | resumable interview state |
| `.careerdocs/layout/` | page renders from the layout check |

Documents are `<Name>-<Org>-<Role>-Resume.docx` and `-Cover.docx`, with a PDF when
LibreOffice is present. In a git workspace `render` commits an uncommitted previous
render before overwriting it and every round ends with `commit`; elsewhere the previous
render moves to `archive/` and `commit` is a no-op.

No applicant data lives in this plugin; `examples/` is a fictional applicant.
