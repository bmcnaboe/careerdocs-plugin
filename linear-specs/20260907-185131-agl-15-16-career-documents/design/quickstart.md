# Quickstart: Portable Resume and Cover-Letter Plugin

## Developer setup

```bash
uv sync --extra dev                  # dev dependencies (pytest, fixture builders)
./scripts/gate.sh basic              # unit tests + skills lint
./scripts/gate.sh full               # + integration runs, inventory and version checks
./scripts/gate.sh final --strict     # + shellcheck, gitleaks, applicant-data guard; SKIP = failure
```

`uv` is the only tool assumed. LibreOffice (`soffice`) is optional: with it, `render --pdf`
converts locally; without it, tests use the committed rendered fixture and the flow asks
the platform to export the PDF.

## End-to-end on the example applicant

All commands run from a scratch copy of the example workspace so the repository stays
untouched:

```bash
cp -R examples/applicant /tmp/cd-demo && cd /tmp/cd-demo
CD=../path/to/skills/career-documents/scripts/careerdocs.py
uv run $CD doctor
uv run $CD profile import sources/*
# The agent turns the emitted candidates into candidates.json (the tests ship one)
uv run $CD profile diff candidates.json          # prints the diff and one conflict question
uv run $CD state answer onboard applicant q-001 "2024-06"
uv run $CD profile approve <diff_id>
uv run $CD profile apply <diff_id>
uv run $CD brief applications/example-role/job-description.md
uv run $CD map --role example-role
uv run $CD plan --role example-role --positioning builder
uv run $CD render --role example-role --kind resume --pdf
uv run $CD check applications/example-role/outputs/resume-*.docx
```

Expected: one conflict question, an applied profile with every entity carrying an ID and
provenance, a role brief with one `gap` requirement, a résumé whose output record shows
five passing checks (link check `skipped` when offline), and page images under
`outputs/layout/`.

## Manual acceptance guidance (residual risk only)

The automated checks cover facts, dates, links, pagination, and layout geometry. What
they cannot judge, and a person should, once per release:

1. **Install, per platform.** On a machine profile with no prior install: follow
   `docs/setup-claude.md`, then `docs/setup-codex.md` (including the ChatGPT upload
   step). Confirm both list the same five skills and that no step outside the documents
   was needed.
2. **Voice.** Run the résumé and cover-letter flows on the example applicant on each
   platform. Read the outputs against `examples/applicant/voice/voice.md`: tone, person,
   banned phrases, sentence shape.
3. **Judgement.** In the requirement-to-evidence map, spot-check that `transferable`
   classifications are defensible and that the letter handles the `gap` honestly.
4. **Layout.** Open the page images under `outputs/layout/` and the DOCX itself; the
   heuristics catch overflow and empty pages, not taste.

Record findings on the ticket, not in the repository.
