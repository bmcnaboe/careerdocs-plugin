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
# The agent turns the emitted text blocks into candidates.json (the tests ship one).
# --flow/--subject persist the generated questions to workflow state; --json prints
# the diff id and the questions to answer.
uv run $CD profile diff candidates.json --flow onboard --subject applicant --json
# Answer each generated question by its id (from the diff output), e.g. the end-date conflict:
uv run $CD state answer onboard applicant --question "conflict:<experience-id>:end_date" --answer "2021-06"
# Re-diff with the resolution, then approve and apply the reviewed diff:
uv run $CD profile approve <diff_id>
uv run $CD profile apply <diff_id>
uv run $CD brief applications/example-role/job-description.md --role-slug example-role
uv run $CD map --role-slug example-role
uv run $CD plan --role-slug example-role --positioning builder --kind resume
uv run $CD render --role-slug example-role --kind resume --pdf
uv run $CD check applications/example-role/outputs/resume-*.docx
```

Expected: one conflict question, an applied profile with every entity carrying an ID and
provenance, a role brief with one `gap` requirement (the FDA-cleared medical-device line),
a résumé whose output record shows five passing checks (the PDF checks `skipped` when
LibreOffice is absent), and page images under `applications/example-role/outputs/layout/`.

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
