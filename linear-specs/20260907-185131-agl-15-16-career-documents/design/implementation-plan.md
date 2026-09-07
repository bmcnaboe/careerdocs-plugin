# Implementation Plan: Portable Resume and Cover-Letter Plugin

**Branch**: `linear/agl-15-16-career-documents` | **Date**: 2026-09-07 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `design/spec.md`; executed by the run plan one level up (`plan.md`)

**Ticket**: AGL-15 (https://linear.app/agent-layer/issue/AGL-15/build-a-portable-resume-and-cover-letter-plugin). Commits reference it as `(AGL-15)`.

## Summary

Build `career-documents` as five Agent Skills in one `skills/` source tree, a Python
CLI (`careerdocs`) that owns every deterministic step (configuration, profile schema and
providers, diff and approval, role brief and evidence-map skeletons, content planning,
DOCX rendering, the five output checks, output records, workflow state), and two thin
packages: the repository itself is the Claude Code/Cowork plugin, and
`packages/openai/` holds a manifest plus a standard-library installer for Codex and
ChatGPT. The structured-Markdown provider is the reference implementation; the Basic
Memory provider writes the same per-entity notes into a vault folder. Applicant data
never enters the repository; a sanitized fictional applicant under `examples/` is the
fixture for every test.

## Technical Context

**Language/Version**: Python 3.11+ (repository tooling standard library only; the runtime CLI declares PEP 723 inline dependencies and runs under `uv run`, with `pip` fallback documented)

**Primary Dependencies**: `docxtpl`, `pypdf`, `pdfplumber`, `pypdfium2`, `jsonschema`, `python-dateutil` (runtime, inline); `pytest`, `reportlab` (dev only, fixture building)

**Storage**: Files. Authoritative profile in the applicant workspace (`profile/`) or a Basic Memory vault folder; JSON artifacts per application; JSON workflow state; JSONL approvals and sources

**Testing**: `pytest` (unit under `tests/unit`, end-to-end CLI runs under `tests/integration` against `examples/`), `shellcheck`, `gitleaks`, in-repo guards (skills lint, applicant-data guard, inventory and version agreement, verification-evidence traceability)

**Target Platform**: macOS and Linux machines running Claude Code, Cowork, Codex, or ChatGPT skill hosts; CI on Ubuntu without LibreOffice

**Project Type**: Agent plugin (Agent Skills plus a CLI); single project

**Performance Goals**: Any CLI command completes in under 5 seconds on a 200-entity profile; render plus checks under 60 seconds excluding PDF conversion

**Constraints**: No applicant data in the repository; no hosted service, UI, or submission; works with no configuration file; offline except optional link checks; the same behavior on both platforms

**Scale/Scope**: One applicant per workspace; up to 1,000 profile entities; up to 100 applications per workspace

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle                                                   | How this plan satisfies it                                                                                                                                                                          | Status |
| ----------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ |
| I. Applicant data never enters the repository               | Fixtures are a fictional applicant under `examples/` and `tests/fixtures/`; `scripts/pii_guard.py` and `gitleaks` run in the final gate; the CLI refuses to write inside the plugin install path       | PASS   |
| II. Four authorities, modeled separately                    | Profile (providers), voice (`voice.md`), templates (`template.docx` + `template.json`), role (`brief.json`) each have their own schema, location, and CLI surface; the config only locates them        | PASS   |
| III. One authoritative profile, approved diffs only         | `providers.authoritative` names one provider; every write is `diff → approve → apply` with hash-bound approvals; content plans cite entity IDs; the factual check rejects unsourced units               | PASS   |
| IV. Provider-neutral source, thin packages                  | All logic in `skills/`; Claude package is two manifests at the root; OpenAI package is a manifest and a standard-library installer; `check_inventory.py` enforces identical inventories                 | PASS   |
| V. Verified output                                          | `careerdocs check` runs factual, links/dates, extraction, pagination, and layout checks and writes the output record; a document is "done" only when the record shows every check passed or skipped with reason | PASS   |
| VI. Simplicity and portability                              | Standard-library tooling; PEP 723 runtime; no service or UI; every third-party dependency ships wheels                                                                                                | PASS   |

Post-design re-check (after Phase 1): unchanged, no violations; Complexity Tracking stays empty.

## Project Structure

### Documentation (this feature)

```text
linear-specs/20260907-185131-agl-15-16-career-documents/
├── plan.md                      # Run plan: 68 tasks in five tranches, ticket snapshots
└── design/
    ├── implementation-plan.md   # This file
    ├── spec.md                  # User stories, requirements, success criteria
    ├── research.md              # Decisions R1–R17
    ├── data-model.md            # Entities, rules, state transitions
    ├── quickstart.md            # Dev setup, end-to-end runs, manual acceptance guidance
    ├── verification-evidence.md # Scenario → method → evidence → status
    └── contracts/               # provider-contract.md, cli.md, artifacts.md, packages.md,
                                 # career-profile.schema.json, config.schema.json
```

### Source Code (repository root)

```text
.claude-plugin/
├── plugin.json                  # Claude Code / Cowork plugin manifest
└── marketplace.json             # Single-plugin marketplace pointing at ./
skills/
├── career-documents/            # Core skill: conventions, schema, providers, checks, doctor
│   ├── SKILL.md
│   ├── agents/openai.yaml
│   ├── references/              # schema.md, provider-contract.md, checks.md, configuration.md
│   ├── assets/schemas/          # career-profile, config, role-brief, requirement-map,
│   │                            # content-plan, output-record, workflow-state (.schema.json)
│   └── scripts/
│       ├── careerdocs.py        # PEP 723 entry point
│       └── careerdocs/          # cli, config, ids, schema, diff, merge, questions, state,
│           ├── providers/       #   base, markdown, basic_memory
│           ├── importers/       #   docx, pdf, network_export, note
│           ├── checks/          #   factual, links_dates, extraction, pagination, layout
│           └── (brief, mapping, plan, render, record).py
├── career-onboard/              # SKILL.md, agents/openai.yaml, references/playbook.md
├── career-update/
├── career-resume/
└── career-cover-letter/
packages/openai/
├── manifest.json                # Skill inventory + version
└── install.py                   # Standard library: link/copy into $HOME/.agents/skills
examples/applicant/              # Fictional applicant: config, profile, sources, voice,
│                                # templates, one application (job description)
docs/                            # setup-claude.md, setup-codex.md, configuration.md,
│                                # profile-schema.md, provider-contract.md, checks.md,
│                                # templates-and-voice.md
scripts/
├── gate.sh                      # basic | full | final [--strict]
├── lint_skills.py               # Agent Skills frontmatter rules
├── pii_guard.py                 # Applicant-data guard
├── check_inventory.py           # Package inventories equal the skills tree
├── check_versions.py            # One version everywhere
├── verification_evidence_check.py
└── build_fixtures.py            # Builds example DOCX/PDF fixtures deterministically
tests/
├── unit/
├── integration/
└── fixtures/                    # rendered/ (committed example PDF), expected outputs
pyproject.toml                   # Version of record; dev extras
LICENSE                          # MIT
README.md
```

**Structure Decision**: Single project. The repository root doubles as the Claude plugin
so `skills/` is consumed in place; all Python lives inside the core skill so a user-scope
install of the skills carries the CLI with it; repository-only tooling stays under
`scripts/` and is never installed.

## Verification Strategy

| Outcome (spec)                                                     | Method                          | Evidence                                                                                              |
| ------------------------------------------------------------------ | ------------------------------- | ----------------------------------------------------------------------------------------------------- |
| US1 both packages expose identical inventories (SC-001)            | contract                        | `scripts/check_inventory.py` in the full gate; `tests/integration/test_packages.py`                   |
| US1 install on Claude / Codex reaches a working state              | smoke + manual-acceptance       | `claude plugin validate .` when the CLI is present; `install.py --home <tmp>` in tests; quickstart §Manual acceptance |
| US1 no applicant data in the repository (SC-002)                   | contract                        | `scripts/pii_guard.py` + `gitleaks` in the final gate                                                 |
| US2 conflict → one question → approved diff → one authoritative entry | integration                  | `tests/integration/test_onboard.py` over `examples/applicant/sources`                                 |
| US2 resume without repeating questions (SC-005)                    | integration                     | same test, interrupted-and-resumed state                                                              |
| US2 private facts absent from exports and documents                | integration                     | `test_onboard.py` export assertions; `test_resume.py` render assertions                               |
| US2 Basic Memory provider holds the same IDs; Markdown export derived | integration                  | `tests/integration/test_basic_memory_provider.py` against a temporary vault folder                    |
| US3 brief → map → plan → render, gap never claimed (SC-003)        | integration                     | `tests/integration/test_resume.py` with the example job description                                   |
| US3 positioning inverts emphasis without changing facts            | unit + integration              | `tests/unit/test_plan.py`; `test_resume.py`                                                           |
| US3 five checks pass on the example (SC-004)                       | integration                     | `test_resume.py` over the committed rendered fixture and a fresh render                               |
| US3 page-budget cuts reported                                      | unit                            | `tests/unit/test_plan.py`                                                                             |
| US4 letter complements, no verbatim bullets, gaps not claimed      | integration                     | `tests/integration/test_cover_letter.py`                                                              |
| US5 update propagates and stale outputs reported (SC-006)          | integration                     | `tests/integration/test_update.py`                                                                    |
| Prose quality in the applicant's voice; transferable-evidence judgement | manual-acceptance          | quickstart §Manual acceptance (residual risk only; facts are covered by the automated checks)         |
| Setup documents are sufficient (SC-007)                            | manual-acceptance               | quickstart §Manual acceptance, one clean install per platform                                         |

## Phase 0 and Phase 1 outputs

- Phase 0: [research.md](research.md), decisions R1–R17, no unresolved unknowns.
- Phase 1: [data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md), [verification-evidence.md](verification-evidence.md).
- Phase 2: the task list lives in the run plan (`../plan.md`), tranches A–D.

## Complexity Tracking

No constitution violations to justify.
