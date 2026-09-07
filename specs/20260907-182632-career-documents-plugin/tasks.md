---
description: "Task list for the portable resume and cover-letter plugin"
---

# Tasks: Portable Resume and Cover-Letter Plugin

**Input**: Design documents from `/specs/20260907-182632-career-documents-plugin/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md, verification-evidence.md

**Tests**: The spec requires automated verification of every acceptance scenario, so test work is bundled inside each implementation task (red→green within the task) and every user-story phase ends with an end-to-end verification task. No standalone test tasks.

**Organization**: Tasks are grouped by user story (spec priorities P1–P3) so each story is an independently verifiable increment.

**Ticket**: AGL-15. Every commit subject ends with `(AGL-15)`; the ticket stays `In Progress` for the whole run; Linear writes are best-effort (on failure, append the reason to `.ralph/errors.log` and keep building).

## Format: `[ID] [P?] [Story?] [risky?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: User story label (US1–US5) for story-phase tasks; omitted for Setup, Foundational, and Polish
- **[risky]**: The task's own diff touches an integration-sensitive surface (skill frontmatter or routing, schemas or provider contract modules, package manifests or installers, gate/policy/CI, or the render/check pipeline entry points); the executor runs `./scripts/gate.sh full` before committing it, `./scripts/gate.sh basic` otherwise
- Paths are repository-relative; the CLI package root is `skills/career-documents/scripts/careerdocs/`

## Path Conventions

- Provider-neutral source: `skills/<skill-name>/` (SKILL.md, agents/openai.yaml, references/, assets/, scripts/)
- Schemas: `skills/career-documents/assets/schemas/`; repository tooling: `scripts/`; tests: `tests/unit/`, `tests/integration/`, `tests/fixtures/`
- Platform packages: `.claude-plugin/` (Claude Code/Cowork), `packages/openai/` (ChatGPT/Codex)
- Sanitized example applicant: `examples/applicant/`; documentation: `docs/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Tooling, guards, and CI so every later task lands against a real gate. `scripts/gate.sh` and `.ralph/command-policy` already exist and report `SKIP` for components created here.

- [ ] T001 [risky] Create `pyproject.toml` (name `career-documents`, version `0.1.0`, `requires-python >= 3.11`, `[project.optional-dependencies] dev` = pytest, jsonschema, docxtpl, python-docx, pypdf, pdfplumber, pypdfium2, python-dateutil, reportlab), run `uv sync --extra dev` and commit `uv.lock`, and add `tests/unit/test_pyproject.py` asserting the file parses with `tomllib` and carries the version, so `./scripts/gate.sh basic` runs the unit suite for real
- [ ] T002 [P] Add `LICENSE` (MIT), `README.md` (what the plugin is, the four flows, the four authorities, the no-applicant-data rule, install pointers to `docs/`), and `docs/README.md` as the documentation index
- [ ] T003 [P] Implement `scripts/pii_guard.py` (standard library; scans `git ls-files` outside `examples/` and `tests/fixtures/` for email addresses not on `example.com`/`example.org`, telephone numbers not using `555`, and street-address patterns; prints `file:line: pattern`; exit 1 on findings) with `tests/unit/test_pii_guard.py`
- [ ] T004 [P] Implement `scripts/lint_skills.py` (standard library flat-YAML frontmatter parser; enforces the Agent Skills rules: `name` matches the directory, 1–64 chars, lowercase/digits/hyphens, no leading, trailing, or double hyphens; `description` 1–1024 chars; `compatibility` ≤ 500; `metadata` string map; body ≤ 500 lines; `agents/openai.yaml` when present is a flat key-value file) with `tests/unit/test_lint_skills.py`
- [ ] T005 [P] Implement `scripts/verification_evidence_check.py` (parses acceptance scenarios from `spec.md` per user story and the rows of `verification-evidence.md`; fails on a scenario without a row or a row without evidence; `--require-complete` additionally fails on any `pending`) with `tests/unit/test_verification_evidence_check.py`
- [ ] T006 [P] Implement `scripts/check_versions.py` (reads the version of record from `pyproject.toml`; requires every `skills/*/SKILL.md` `metadata.version` to equal it; compares `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, and `packages/openai/manifest.json` when present and reports which manifests are absent) with `tests/unit/test_check_versions.py`
- [ ] T007 [risky] Add `.github/workflows/ci.yml` (ubuntu-latest; checkout; `astral-sh/setup-uv`; `uv sync --extra dev`; install shellcheck and gitleaks; run `./scripts/gate.sh final`) so every push and pull request runs the full bar
- [ ] T008 Post a start comment on AGL-15 naming the run branch and the plan path (Linear MCP; best-effort, log failures to `.ralph/errors.log`)

**Checkpoint**: `./scripts/gate.sh final` runs unit tests, the four guards, shellcheck, gitleaks, and conformance with no `FAIL` lines.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The core skill, schemas, CLI skeleton, providers, diffs, state, and the fixture applicant that every story depends on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T009 [risky] Create `skills/career-documents/SKILL.md` (core conventions: the four authorities and where each lives, how flow skills invoke `careerdocs`, the diff-then-approve rule, visibility semantics, where state and outputs go), `skills/career-documents/agents/openai.yaml`, `skills/career-documents/assets/schemas/career-profile.schema.json` and `config.schema.json` (copied from `specs/20260907-182632-career-documents-plugin/contracts/`), and `skills/career-documents/references/schema.md`
- [ ] T010 Create `skills/career-documents/scripts/careerdocs.py` (PEP 723 header declaring docxtpl, pypdf, pdfplumber, pypdfium2, jsonschema, python-dateutil; delegates to `careerdocs.cli:main`) and `skills/career-documents/scripts/careerdocs/cli.py` (argparse with `--workspace`, `--json`, exit codes 0/1/2, `version`, a minimal `doctor`) with `tests/unit/test_cli.py`
- [ ] T011 Implement `skills/career-documents/scripts/careerdocs/config.py` (defaults for every key, load and validate against `config.schema.json`, refusal of credential-like or qualification-like keys, `config init` and `config validate` subcommands) with `tests/unit/test_config.py`
- [ ] T012 Implement `skills/career-documents/scripts/careerdocs/ids.py` (ULID generation and `<type>_<ULID>` parsing) and `skills/career-documents/scripts/careerdocs/schema.py` (jsonschema validation plus semantic rules: date order, no future dates, reference resolution, single contact, unresolved conflicts block their field) with `tests/unit/test_schema.py`
- [ ] T013 [risky] Implement `skills/career-documents/scripts/careerdocs/providers/base.py` (the provider interface and typed errors from the provider contract) and `skills/career-documents/scripts/careerdocs/providers/markdown.py` (index and per-entity files, `sources.jsonl`, `approvals.jsonl`, `diffs/`, canonical hash, read, export) with `tests/unit/test_markdown_provider.py`
- [ ] T014 Implement `skills/career-documents/scripts/careerdocs/providers/basic_memory.py` (per-entity Basic Memory notes with the schema fields in frontmatter, `## Observations` and `## Relations` sections, `<folder>/<type>/<id>` permalinks; read back; export to the Markdown layout with `derived: true`) with `tests/unit/test_basic_memory_provider.py`
- [ ] T015 Implement `skills/career-documents/scripts/careerdocs/diff.py` (ProfileDiff operations, `base_hash`, Markdown rendering, `profile diff`, `profile approve` writing hash-bound approvals, `profile apply` refusing on missing approval or base-hash mismatch and refreshing derived exports, `profile validate`, `profile export`) with `tests/unit/test_diff.py`
- [ ] T016 Implement `skills/career-documents/scripts/careerdocs/state.py` (WorkflowState per flow and subject, append-only questions that are never asked twice, `state show`, `state answer`, `state resume`) with `tests/unit/test_state.py`
- [ ] T017 Create the fictional example applicant: `scripts/build_fixtures.py` (deterministic; builds `examples/applicant/sources/resume-a.docx` with python-docx and `resume-b.pdf` with reportlab, the two disagreeing on one end date) plus the committed `examples/applicant/career-documents.json`, `voice/voice.md`, `sources/network-export.csv`, `sources/voice-note.md`, `applications/example-role/job-description.md` (with one requirement the profile cannot meet), and `tests/fixtures/candidates.json` (the extracted candidate set containing the deliberate conflict)

**Checkpoint**: `careerdocs doctor`, `config`, `profile validate|diff|approve|apply|export`, and `state` work against the example workspace in a temporary copy; both providers round-trip the example profile.

---

## Phase 3: User Story 1 - Install the plugin and see the same flows everywhere (Priority: P1) 🎯 MVP

**Goal**: Both platform packages exist, install cleanly, and expose an identical skill inventory; the repository provably holds no applicant data.

**Independent Test**: Build inventories from `skills/` and both manifests and compare; install the OpenAI package into a temporary home; run the applicant-data guard.

- [ ] T018 [US1] [risky] Create `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` (single plugin, `source: "./"`) and implement `scripts/check_inventory.py` (skills tree versus the Claude manifest; runs `claude plugin validate .` when the CLI is on PATH) with `tests/unit/test_check_inventory.py`
- [ ] T019 [US1] [risky] Create `packages/openai/manifest.json` and `packages/openai/install.py` (standard library; `--link` default, `--copy`, `--home`, `--dry-run`, `--uninstall`; targets `$HOME/.agents/skills/`; prints the ChatGPT skill-upload steps; exits non-zero when the manifest disagrees with `skills/`) with `tests/unit/test_install.py`; extend `scripts/check_inventory.py` to compare the OpenAI manifest and `scripts/check_versions.py` to require both manifests
- [ ] T020 [P] [US1] Write `docs/setup-claude.md` (marketplace add, plugin install, Cowork note, verification via `claude plugin details`) and `docs/setup-codex.md` (installer usage, ChatGPT upload, verification via `ls ~/.agents/skills`), and the README install section
- [ ] T021 [US1] Update `specs/20260907-182632-career-documents-plugin/verification-evidence.md` with the US1 outcome map, automated guard evidence, and generated artifact links
- [ ] T022 [US1] [risky] Verify US1: `tests/integration/test_packages.py` builds the inventory from `skills/` and both manifests and asserts zero differences, runs `packages/openai/install.py --link --home <tmp>` and asserts every installed `SKILL.md` is byte-identical to its source and that the install contains no applicant data, runs `scripts/pii_guard.py` over tracked files asserting zero findings, and runs `claude plugin validate .` when available. Test exercises the real files, not mocked manifests.

**Checkpoint**: Both packages install from the repository; inventories match; the guard is green.

---

## Phase 4: User Story 2 - Onboard existing material into one authoritative profile (Priority: P1)

**Goal**: Sources in, one approved profile out, with provenance, conflicts resolved by exactly one question each, resumability, and visibility respected on both providers.

**Independent Test**: Run the onboarding CLI sequence on the example sources with the shipped candidate set, interrupt and resume, approve, apply, export; repeat with Basic Memory authoritative in a temporary vault.

- [ ] T023 [US2] Implement `skills/career-documents/scripts/careerdocs/importers/` (`docx.py`, `pdf.py`, `network_export.py`, `note.py`) and `profile import` (registers sources with sha256 in `sources.jsonl`, emits text blocks and candidate skeletons as JSON) with `tests/unit/test_importers.py` over `examples/applicant/sources/`
- [ ] T024 [US2] Implement `skills/career-documents/scripts/careerdocs/merge.py` (candidates → deduplication keys per type, precedence order, conflict candidates → ProfileDiff via `profile diff`) with `tests/unit/test_merge.py` asserting the two disagreeing résumés yield one experience with both provenance entries and exactly one conflict
- [ ] T025 [US2] Implement `skills/career-documents/scripts/careerdocs/questions.py` (materiality rules; questions generated from conflicts, missing dates, and visibility defaults; persisted through `state.py`; answers become `resolve_conflict` or `update_field` operations) with `tests/unit/test_questions.py` asserting no question repeats after a resume
- [ ] T026 [US2] Implement visibility filtering (`visible_for(document)` in the providers and exports, `restricted` per-document approvals via `profile approve --document`, `derived: true` labeling on every export) with `tests/unit/test_visibility.py`
- [ ] T027 [US2] [risky] Create `skills/career-onboard/SKILL.md`, `skills/career-onboard/agents/openai.yaml`, and `skills/career-onboard/references/playbook.md` (inventory sources → `profile import` → extract candidates into `candidates.json` against the schema → `profile diff` → ask only the generated questions → `profile approve` after an explicit yes → `profile apply` → `profile export`), and add the skill to both package manifests
- [ ] T028 [US2] Update `specs/20260907-182632-career-documents-plugin/verification-evidence.md` with the US2 outcome map, automated guard evidence, and generated artifact links
- [ ] T029 [US2] [risky] Verify US2: `tests/integration/test_onboard.py` runs import → diff → one question → answer → approve → apply → export on the example sources and asserts one role entry with both provenance entries and `applicant_verified`, resumes an interrupted run without repeating the question, and confirms a private fact is absent from the export; `tests/integration/test_basic_memory_provider.py` repeats the sequence with `authoritative: basic_memory` in a temporary vault and asserts the same IDs in the notes and a `derived: true` Markdown export. Tests exercise the real CLI and files, not mocked providers.

**Checkpoint**: Onboarding produces one authoritative profile on either provider.

---

## Phase 5: User Story 3 - Generate a tailored résumé for a job description (Priority: P2)

**Goal**: Job description in, checked résumé out, with every claim traceable and gaps never claimed.

**Independent Test**: Run brief → map → plan → render → check on the example job description that contains one unmet requirement.

- [ ] T030 [US3] Implement `skills/career-documents/scripts/careerdocs/brief.py` (`brief`: job description from file or URL text; requirement skeletons with stable ids and must/nice kind; keyword extraction; positioning recommendation; validation of the agent-completed brief) and `skills/career-documents/assets/schemas/role-brief.schema.json` with `tests/unit/test_brief.py`
- [ ] T031 [US3] Implement `skills/career-documents/scripts/careerdocs/mapping.py` (`map`: candidate evidence per requirement by keyword and skill overlap; validation that every requirement appears exactly once, `gap` entries have no evidence, classifications are valid) and `skills/career-documents/assets/schemas/requirement-map.schema.json` with `tests/unit/test_mapping.py`
- [ ] T032 [US3] Implement `skills/career-documents/scripts/careerdocs/plan.py` (`plan`: selection, ordering, and emphasis by positioning tags; page-budget estimate from the template manifest; cut list; units carrying `source_ids`; template allowlist) and `skills/career-documents/assets/schemas/content-plan.schema.json` with `tests/unit/test_plan.py` (`test_positioning_inverts`, `test_budget_cuts_reported`)
- [ ] T033 [US3] [risky] Implement `skills/career-documents/scripts/careerdocs/render.py` (`render`: docxtpl rendering from the content plan and voice profile into the template; timestamped output naming; output-record skeleton; `--pdf` via `soffice` when present, reported when absent) and the example résumé template `examples/applicant/templates/resume/template.docx` + `template.json` built by `scripts/build_fixtures.py`, with `tests/unit/test_render.py`
- [ ] T034 [US3] Implement `skills/career-documents/scripts/careerdocs/checks/factual.py` (unit matching, token traceability of numbers, dates, organizations, and titles to cited entities, template allowlist) and `skills/career-documents/scripts/careerdocs/checks/links_dates.py` (date parsing, ordering, no future dates; link syntax; optional network check recorded as `skipped` offline) with `tests/unit/test_checks_factual.py`
- [ ] T035 [US3] Implement `skills/career-documents/scripts/careerdocs/checks/extraction.py`, `pagination.py`, and `layout.py` (pypdf text extraction; page count against the budget; pdfplumber margin and density heuristics; pypdfium2 page PNGs) with the committed fixture `tests/fixtures/rendered/example-resume.pdf` and `tests/unit/test_checks_layout.py`
- [ ] T036 [US3] Implement `skills/career-documents/scripts/careerdocs/record.py` (`check`: runs the five checks, writes the OutputRecord, exit codes) and `skills/career-documents/assets/schemas/output-record.schema.json` with `tests/unit/test_record.py`
- [ ] T037 [US3] [risky] Create `skills/career-resume/SKILL.md`, `skills/career-resume/agents/openai.yaml`, and `skills/career-resume/references/playbook.md` (brief → complete requirements → map with direct/transferable/gap judgement → choose positioning → plan → draft units in voice → render → check → report cuts and gaps), and add the skill to both package manifests
- [ ] T038 [US3] Update `specs/20260907-182632-career-documents-plugin/verification-evidence.md` with the US3 outcome map, automated guard evidence, and generated artifact links
- [ ] T039 [US3] [risky] Verify US3: `tests/integration/test_resume.py` runs brief → map → plan → render → check on the example job description and asserts the four artifacts exist in order, the unmet requirement is a `gap` and no rendered sentence claims it, switching positioning inverts emphasis without changing any fact, all five checks report `pass` (link check `pass` or `skipped` offline), and page-budget cuts are reported. Test exercises the real CLI, template, and rendered files, not mocked dependencies.

**Checkpoint**: The example résumé renders and passes every check.

---

## Phase 6: User Story 4 - Generate a complementary cover letter (Priority: P3)

**Goal**: A checked letter that reuses the role brief and map, complements the résumé, and never claims a gap.

**Independent Test**: Generate the letter for the example role after the résumé and run the checks.

- [ ] T040 [US4] Extend `skills/career-documents/scripts/careerdocs/plan.py` with `--kind cover_letter` (paragraph units, top requirements by value, gap policy, exclusion of verbatim résumé bullets, letter page budget) with additions to `tests/unit/test_plan.py`
- [ ] T041 [US4] Add the example letter template `examples/applicant/templates/cover-letter/template.docx` + `template.json` to `scripts/build_fixtures.py`, support `render --kind cover_letter`, and add the verbatim-bullet check to `skills/career-documents/scripts/careerdocs/checks/factual.py` with additions to `tests/unit/test_render.py` and `tests/unit/test_checks_factual.py`
- [ ] T042 [US4] [risky] Create `skills/career-cover-letter/SKILL.md`, `skills/career-cover-letter/agents/openai.yaml`, and `skills/career-cover-letter/references/playbook.md` (reuse brief and map without re-asking; draft in voice; complement, do not repeat; handle gaps honestly), and add the skill to both package manifests
- [ ] T043 [US4] Update `specs/20260907-182632-career-documents-plugin/verification-evidence.md` with the US4 outcome map, automated guard evidence, and generated artifact links
- [ ] T044 [US4] [risky] Verify US4: `tests/integration/test_cover_letter.py` generates the letter for the example role after the résumé and asserts the brief and map are reused with zero new questions, every claim traces to a profile ID, the gap requirement is not claimed, the letter fits its page budget, and no résumé bullet appears verbatim. Test exercises the real CLI and rendered files.

**Checkpoint**: Résumé and letter for the example role both pass their checks.

---

## Phase 7: User Story 5 - Update qualifications after onboarding (Priority: P3)

**Goal**: Changes flow through the same diff-and-approve path, exports stay in agreement, and stale outputs are named.

**Independent Test**: Change one end date in the example profile through the update path and observe the export and the stale report.

- [ ] T045 [US5] Extend `profile apply` in `skills/career-documents/scripts/careerdocs/diff.py` to mark output records whose `source_ids` include a changed entity as stale (with reason) and implement `profile status` (stale outputs, derived export freshness) with additions to `tests/unit/test_diff.py`
- [ ] T046 [US5] [risky] Create `skills/career-update/SKILL.md`, `skills/career-update/agents/openai.yaml`, and `skills/career-update/references/playbook.md` (capture the statement with provenance → candidates → `profile diff` → approve → apply → report stale outputs; resume from pending diff), and add the skill to both package manifests
- [ ] T047 [US5] Update `specs/20260907-182632-career-documents-plugin/verification-evidence.md` with the US5 outcome map, automated guard evidence, and generated artifact links
- [ ] T048 [US5] [risky] Verify US5: `tests/integration/test_update.py` applies an update that changes one end date and adds one achievement, and asserts the new fact carries a fresh ID, statement provenance, and `applicant_verified`, the authoritative profile and the derived export agree, the earlier example résumé's output record is reported stale, and an interrupted update resumes to the same pending diff without re-asking. Test exercises the real CLI and files.

**Checkpoint**: All five skills exist, both manifests list them, and every story's verification passes.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, the core skill's reference material, evidence completeness, and the strict final gate.

- [ ] T049 [P] Write `docs/configuration.md`, `docs/profile-schema.md`, and `docs/provider-contract.md` from the contracts and the shipped schemas
- [ ] T050 [P] Write `docs/checks.md` and `docs/templates-and-voice.md`, and complete `README.md` (flows, platforms, privacy model, links to every document)
- [ ] T051 Complete `skills/career-documents/references/provider-contract.md`, `references/checks.md`, `references/configuration.md`, and the `doctor` command (converter detection, dependency status, provider reachability, template and voice presence) with additions to `tests/unit/test_cli.py`
- [ ] T052 Run `python3 scripts/verification_evidence_check.py --require-complete`, resolve every traceability gap in `specs/20260907-182632-career-documents-plugin/verification-evidence.md`, and finalize the manual-acceptance guidance in `specs/20260907-182632-career-documents-plugin/quickstart.md`
- [ ] T053 [risky] Switch `.github/workflows/ci.yml` to `./scripts/gate.sh final --strict` and remove every remaining `SKIP` by adding the missing component, never by loosening the gate
- [ ] T054 Post a summary comment on AGL-15 (what landed, how to verify) and move it to `In Review` (Linear MCP; best-effort, log failures to `.ralph/errors.log`)
- [ ] T055 [risky] Verify `./scripts/gate.sh final --strict` passes end to end; if any guard fires, fix the underlying issue (no bypass)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; T001 first (it makes the unit suite real), then T002–T007 in parallel, T008 last
- **Foundational (Phase 2)**: Depends on Setup; T009 → T010 → T011 → T012 → T013 → T014 → T015 → T016 → T017; blocks all user stories
- **US1 (Phase 3)**: Depends on Foundational; T018 → T019, T020 in parallel with T019, then T021 → T022
- **US2 (Phase 4)**: Depends on Foundational; T023 → T024 → T025 → T026 → T027 → T028 → T029
- **US3 (Phase 5)**: Depends on US2 (needs an approved profile); T030 → T031 → T032 → T033 → T034 → T035 → T036 → T037 → T038 → T039
- **US4 (Phase 6)**: Depends on US3 (reuses brief, map, render, checks); T040 → T041 → T042 → T043 → T044
- **US5 (Phase 7)**: Depends on US3 (stale marking needs output records); T045 → T046 → T047 → T048
- **Polish (Phase 8)**: Depends on every story; T049 and T050 in parallel, then T051 → T052 → T053 → T054 → T055

### Within Each User Story

- Schemas and models before services; services before flow skills; the flow skill before the evidence update; the verification task always last and always passing before the phase is complete

### Parallel Opportunities

- Phase 1: T002, T003, T004, T005, T006 touch disjoint files
- Phase 3: T020 alongside T019
- Phase 8: T049 alongside T050

## Implementation Strategy

1. Setup and Foundational: a real gate, the schema, both providers, diffs, state, and the fixture applicant
2. US1: installable packages with identical inventories (MVP for the portability promise)
3. US2: one authoritative profile from real sources
4. US3: the tailored résumé with checks (the primary value)
5. US4 and US5: the letter and the update path, reusing everything above
6. Polish: documentation, evidence completeness, strict final gate

## Notes

- [P] tasks touch different files and have no dependency on incomplete tasks
- Every task is one commit: `<type>(<scope>): <description> (AGL-15)`
- Each user-story phase ends with a verification-evidence update and a `[risky]` end-to-end verification
- Agent-driven judgement (extracting facts, classifying evidence, drafting prose) is described in each skill's playbook; the CLI validates and persists what the agent produces
