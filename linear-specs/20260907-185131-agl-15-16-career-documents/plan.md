# Linear run — agl-15-16-career-documents

**Tickets:** AGL-15, AGL-16 · **Created:** 2026-09-07
**Branch:** linear/agl-15-16-career-documents
**Recommended:** model and effort defaults (top tier, `xhigh`) · RALPH_ITERATIONS=40 · RALPH_EVAL_MAX_LOOPS=10
**Verify groups:** A: AGL-15 · B: AGL-16 ← tranche-aligned; the verify loop uses these to batch linear-accept runs.

## Execution

You are executing a batched Linear-ticket run inside the Ralph loop. Work every
remaining unchecked task in order, in a single continuous turn. Commit, read the
next task, keep going — the loop handles rotation; you handle the work.

The framing above owns the stop conditions, the after-every-commit breadcrumb
checks, the handoff contract, and the gate runner — follow it; none of that is
restated here.

Per task:

1. Read only what the task references (the Tickets section below carries each
   ticket's acceptance criteria); implement the minimum change that satisfies it.
   A task that says "Spec T0NN" carries its full description in
   `specs/20260907-182632-career-documents-plugin/tasks.md`: read that entry before
   starting, follow its paths and test names, and mark it `[x]` there in the same
   commit so the spec's checklist stays in step with this plan. The spec's plan,
   research, data model, and contracts in that directory are the design of record.
2. Run the basic gate. Mark `[x]` only after it exits 0 — never around a red gate.
3. `git add <exact paths> && git commit -m "<type>(<scope>): <desc> (AGL-N T###)"`.
   No agent footers, no `--amend`. Then the framing's after-commit checks decide:
   yield or read the next task.

Tranche-close tasks (marked `[risky]`) additionally: the full gate must be green,
then sync Linear for that tranche's tickets as the task describes. Tasks marked
`[risky]` inside a tranche also run the full gate before their commit.

Linear protocol: the Linear MCP tools are usually deferred — load them via
ToolSearch (keyword `linear`) on first use. Every ticket here is in the workspace
pinned in `.claude/linear-workspace.md` (workspace slug `agent-layer`, team
`agent-layer`); the tools take no workspace parameter, so before the first write
confirm a fetched issue's url starts with `https://linear.app/agent-layer/`, and
pass `team: "agent-layer"` on calls that accept it. A connector scoped to another
workspace is not a best-effort failure: skip Linear writes entirely and log it,
rather than writing to the wrong tracker. Otherwise Linear writes are best-effort:
if a Linear call fails (including a connector that cannot authenticate in this
worktree), log it to `.ralph/errors.log` and keep building — never block code work
on the tracker. Catch up missed syncs at the next tranche boundary. To claim a
ticket, post the start comment first and use the returned comment's `author.id` as
the assignee; never guess an agent identity.
Status ceiling during this loop is `In Review`; never touch `Agent Reviewed` or
`Done`.

Tranche E rules (AGL-16 works on applicant data outside the repository):

- **Workspace**: `$HOME/development/career-workspace`, a copy of the applicant's
  "Resumes and Cover Letters" folder that the operator made before launch. If it is
  missing or has no `resume_source_of_truth.md`, emit `<ralph>GUTTER</ralph>` with
  that root cause; never substitute another folder. Every `careerdocs` call in the
  tranche passes `--workspace` with that path.
- **Basic Memory**: vault `$HOME/development/Oxford Heavy/shared-memory`, project
  `shared-memory`, folder `career/`, configured as the authoritative provider with
  the structured-Markdown export at `profile/` as the derived copy. Write through
  the plugin's provider; use the Basic Memory MCP tools for search and context only.
- **Precedence**: register `resume_source_of_truth.md` as the applicant statement
  source (highest precedence). The confirmed facts that must survive the migration
  are listed in AGL-16's description; check each is present and
  `applicant_verified` after apply. If Linear is unreachable, treat
  `resume_source_of_truth.md` as that list.
- **Approval**: the migration diff is pre-authorized by the operator's launch of this
  run. Record it with `profile approve <diff_id> --note "pre-authorized at run launch
  (AGL-16)"`, then post the rendered diff and every open conflict to AGL-16 so the
  applicant reviews it after the fact. A conflict precedence cannot settle stays
  open, which blocks its field from documents; never guess a fact.
- **Privacy**: nothing from the workspace or the vault enters the repository — no
  fixtures, no examples, no applicant paths in documentation beyond the generic
  playbook. The applicant-data guard in the final gate enforces this.
- **Converter**: pagination and layout checks need a PDF. With `soffice` on PATH,
  `render --pdf` produces it. If it is absent, record those checks as skipped with
  the reason, say so in the tranche-close comment, and do not archive the previous
  current-state artifacts (AC5 orders the checks before the archive).

When every task is `[x]` and the full gate is green, emit
`<promise>ALL_TASKS_DONE</promise>`. Genuinely stuck after honest investigation:
emit `<ralph>GUTTER</ralph>` with the root cause.

## Tasks

### Tranche A — Foundation: tooling, guards, core skill, schema, providers, fixtures (AGL-15)

- [ ] T001 [AGL-15] Claim tranche: post the start comment on AGL-15 naming branch `linear/agl-15-16-career-documents` and this plan; capture the comment's `author.id`; ensure AGL-15 is In Progress with that assignee (it may already be, then only the comment is new). Covers spec T008.
- [ ] T002 [AGL-15] [risky] Spec T001 — `pyproject.toml` (version 0.1.0, dev extras), `uv.lock`, `tests/unit/test_pyproject.py`, so the basic gate runs the unit suite for real
- [ ] T003 [AGL-15] Spec T002 — `LICENSE` (MIT), `README.md`, `docs/README.md`
- [ ] T004 [AGL-15] Spec T003 — `scripts/pii_guard.py` with `tests/unit/test_pii_guard.py`
- [ ] T005 [AGL-15] Spec T004 — `scripts/lint_skills.py` with `tests/unit/test_lint_skills.py`
- [ ] T006 [AGL-15] Spec T005 — `scripts/verification_evidence_check.py` with `tests/unit/test_verification_evidence_check.py`
- [ ] T007 [AGL-15] Spec T006 — `scripts/check_versions.py` with `tests/unit/test_check_versions.py`
- [ ] T008 [AGL-15] [risky] Spec T007 — `.github/workflows/ci.yml` running the final gate
- [ ] T009 [AGL-15] [risky] Spec T009 — `skills/career-documents/SKILL.md`, `agents/openai.yaml`, `assets/schemas/career-profile.schema.json` and `config.schema.json`, `references/schema.md`
- [ ] T010 [AGL-15] Spec T010 — `skills/career-documents/scripts/careerdocs.py` (PEP 723) and `careerdocs/cli.py` with `tests/unit/test_cli.py`
- [ ] T011 [AGL-15] Spec T011 — `careerdocs/config.py` with `tests/unit/test_config.py`
- [ ] T012 [AGL-15] Spec T012 — `careerdocs/ids.py` and `careerdocs/schema.py` with `tests/unit/test_schema.py`
- [ ] T013 [AGL-15] [risky] Spec T013 — `careerdocs/providers/base.py` and `providers/markdown.py` with `tests/unit/test_markdown_provider.py`
- [ ] T014 [AGL-15] Spec T014 — `careerdocs/providers/basic_memory.py` with `tests/unit/test_basic_memory_provider.py`
- [ ] T015 [AGL-15] Spec T015 — `careerdocs/diff.py` (`profile diff|approve|apply|validate|export`) with `tests/unit/test_diff.py`
- [ ] T016 [AGL-15] Spec T016 — `careerdocs/state.py` with `tests/unit/test_state.py`
- [ ] T017 [AGL-15] Spec T017 — `scripts/build_fixtures.py`, the fictional applicant under `examples/applicant/`, and `tests/fixtures/candidates.json`
- [ ] T018 [AGL-15] [risky] Close tranche A: full gate green; comment on AGL-15 summarizing what landed (commits, surfaces); AGL-15 stays In Progress

### Tranche B — Packages and onboarding (AGL-15)

- [ ] T019 [AGL-15] [risky] Spec T018 — `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `scripts/check_inventory.py` with `tests/unit/test_check_inventory.py`
- [ ] T020 [AGL-15] [risky] Spec T019 — `packages/openai/manifest.json` and `install.py` with `tests/unit/test_install.py`; inventory and version checks cover both manifests
- [ ] T021 [AGL-15] Spec T020 — `docs/setup-claude.md`, `docs/setup-codex.md`, README install section
- [ ] T022 [AGL-15] Spec T021 — `specs/20260907-182632-career-documents-plugin/verification-evidence.md`: US1 outcome map
- [ ] T023 [AGL-15] [risky] Spec T022 — Verify US1: `tests/integration/test_packages.py` over the real manifests and installer
- [ ] T024 [AGL-15] Spec T023 — `careerdocs/importers/` and `profile import` with `tests/unit/test_importers.py`
- [ ] T025 [AGL-15] Spec T024 — `careerdocs/merge.py` with `tests/unit/test_merge.py`
- [ ] T026 [AGL-15] Spec T025 — `careerdocs/questions.py` with `tests/unit/test_questions.py`
- [ ] T027 [AGL-15] Spec T026 — visibility filtering, per-document approvals, derived labeling with `tests/unit/test_visibility.py`
- [ ] T028 [AGL-15] [risky] Spec T027 — `skills/career-onboard/` (SKILL.md, `agents/openai.yaml`, `references/playbook.md`); both package manifests updated
- [ ] T029 [AGL-15] Spec T028 — verification-evidence.md: US2 outcome map
- [ ] T030 [AGL-15] [risky] Spec T029 — Verify US2: `tests/integration/test_onboard.py` and `tests/integration/test_basic_memory_provider.py`
- [ ] T031 [AGL-15] [risky] Close tranche B: full gate green; progress comment on AGL-15

### Tranche C — Tailored résumé (AGL-15)

- [ ] T032 [AGL-15] Spec T030 — `careerdocs/brief.py` and `assets/schemas/role-brief.schema.json` with `tests/unit/test_brief.py`
- [ ] T033 [AGL-15] Spec T031 — `careerdocs/mapping.py` and `assets/schemas/requirement-map.schema.json` with `tests/unit/test_mapping.py`
- [ ] T034 [AGL-15] Spec T032 — `careerdocs/plan.py` and `assets/schemas/content-plan.schema.json` with `tests/unit/test_plan.py`
- [ ] T035 [AGL-15] [risky] Spec T033 — `careerdocs/render.py` and the example résumé template with `tests/unit/test_render.py`
- [ ] T036 [AGL-15] Spec T034 — `careerdocs/checks/factual.py` and `checks/links_dates.py` with `tests/unit/test_checks_factual.py`
- [ ] T037 [AGL-15] Spec T035 — `checks/extraction.py`, `checks/pagination.py`, `checks/layout.py`, the committed rendered fixture PDF, with `tests/unit/test_checks_layout.py`
- [ ] T038 [AGL-15] Spec T036 — `careerdocs/record.py` and `assets/schemas/output-record.schema.json` with `tests/unit/test_record.py`
- [ ] T039 [AGL-15] [risky] Spec T037 — `skills/career-resume/` (SKILL.md, `agents/openai.yaml`, `references/playbook.md`); both manifests updated
- [ ] T040 [AGL-15] Spec T038 — verification-evidence.md: US3 outcome map
- [ ] T041 [AGL-15] [risky] Spec T039 — Verify US3: `tests/integration/test_resume.py`
- [ ] T042 [AGL-15] [risky] Close tranche C: full gate green; progress comment on AGL-15

### Tranche D — Cover letter, updates, polish (AGL-15)

- [ ] T043 [AGL-15] Spec T040 — letter mode in `careerdocs/plan.py` with additions to `tests/unit/test_plan.py`
- [ ] T044 [AGL-15] Spec T041 — example letter template, `render --kind cover_letter`, verbatim-bullet check, with tests
- [ ] T045 [AGL-15] [risky] Spec T042 — `skills/career-cover-letter/` (SKILL.md, `agents/openai.yaml`, `references/playbook.md`); both manifests updated
- [ ] T046 [AGL-15] Spec T043 — verification-evidence.md: US4 outcome map
- [ ] T047 [AGL-15] [risky] Spec T044 — Verify US4: `tests/integration/test_cover_letter.py`
- [ ] T048 [AGL-15] Spec T045 — stale marking on `profile apply` and `profile status` with additions to `tests/unit/test_diff.py`
- [ ] T049 [AGL-15] [risky] Spec T046 — `skills/career-update/` (SKILL.md, `agents/openai.yaml`, `references/playbook.md`); both manifests updated
- [ ] T050 [AGL-15] Spec T047 — verification-evidence.md: US5 outcome map
- [ ] T051 [AGL-15] [risky] Spec T048 — Verify US5: `tests/integration/test_update.py`
- [ ] T052 [AGL-15] Spec T049 — `docs/configuration.md`, `docs/profile-schema.md`, `docs/provider-contract.md`
- [ ] T053 [AGL-15] Spec T050 — `docs/checks.md`, `docs/templates-and-voice.md`, README complete
- [ ] T054 [AGL-15] Spec T051 — core skill references and the complete `doctor` with additions to `tests/unit/test_cli.py`
- [ ] T055 [AGL-15] Spec T052 — `verification_evidence_check.py --require-complete` reports zero gaps; quickstart manual-acceptance guidance final
- [ ] T056 [AGL-15] [risky] Spec T053 — CI on `final --strict`; every remaining SKIP resolved by adding the component
- [ ] T057 [AGL-15] [risky] Close tranche D: full gate green in strict mode (spec T055); comment on AGL-15 summarizing what landed and how to verify it, and move AGL-15 to In Review (spec T054)

### Tranche E — Migrate the applicant workspace (AGL-16)

- [ ] T058 [AGL-16] Claim tranche: confirm the workspace copy exists per the Tranche E rules (GUTTER if not); post the start comment on AGL-16 naming the branch and this plan; move AGL-16 to In Progress with the comment author as assignee
- [ ] T059 [AGL-16] Implement `careerdocs inventory <dir>` in `skills/career-documents/scripts/careerdocs/inventory.py` (classifies every file as authoritative data, source evidence, template/voice input, generated output, historical record, duplicate by sha256, temporary, or unrelated; writes `inventory.json` and `inventory.md` with a proposed recoverable destination per file) with `tests/unit/test_inventory.py` on a fixture tree
- [ ] T060 [AGL-16] Implement `careerdocs organize --inventory <file> [--apply|--rollback] [--dry-run]` in `skills/career-documents/scripts/careerdocs/organize.py` (moves files into the documented structure `sources/`, `templates/`, `voice/`, `baselines/`, `applications/`, `archive/`, `.career-documents/`; never deletes; every move recorded in `.career-documents/moves.jsonl`; rollback replays it) with `tests/unit/test_organize.py`
- [ ] T061 [AGL-16] Run `careerdocs inventory` on the workspace, review the classification for sense (résumés are source evidence, `output/pdf` copies are duplicates, the Linear draft is temporary, non-career archive items are unrelated), save `inventory.md` in the workspace, and post the class counts to AGL-16
- [ ] T062 [AGL-16] Write the workspace `career-documents.json` (Basic Memory authoritative per the Tranche E rules; Markdown export at `profile/`; templates, voice, outputs, and state paths), run `config validate` and `doctor`, and post the doctor summary to AGL-16
- [ ] T063 [AGL-16] Onboard the applicant: `profile import` over `resume_source_of_truth.md` (registered as the applicant statement source), every current and archived résumé, the LinkedIn export, and notes; extract candidates; `profile diff`; resolve conflicts by precedence and leave the rest open; approve under the launch pre-authorization; `profile apply` (Basic Memory notes plus the derived Markdown export); confirm every confirmed fact from AGL-16's description is present and `applicant_verified`; post the rendered diff and open conflicts to AGL-16
- [ ] T064 [AGL-16] Capture voice and template: draft `voice/voice.md` from the current résumés and `held_sleep_brand_guidelines.md`; convert the current résumé DOCX into `templates/resume/template.docx` + `template.json` (styles kept, content replaced by placeholders, two-page budget) and derive `templates/cover-letter/`; `doctor` reports both present
- [ ] T065 [AGL-16] Generate baselines: `plan` and `render --pdf` for executive and builder into `baselines/<positioning>/`, then `check` each; all five checks pass (link check may be skipped offline; pagination and layout must run, see the converter rule); output records written
- [ ] T066 [AGL-16] Organize the workspace: `organize --apply` with the reviewed inventory; archive the previous current-state artifacts only if every T065 check passed; write the workspace `README.md` describing the structure; confirm `moves.jsonl` covers every relocation and `organize --rollback --dry-run` is clean
- [ ] T067 [AGL-16] Add `docs/migration.md` to the repository (generic playbook: inventory → configure → onboard → capture voice and template → baselines → organize; no applicant specifics) and confirm the applicant-data guard is green
- [ ] T068 [AGL-16] [risky] Close tranche E: full gate green; comment on AGL-16 summarizing the workspace structure, the note count in Basic Memory, the baseline check results, and any open conflicts or skipped checks; move AGL-16 to In Review

## Tickets

### AGL-15 — Build a portable resume and cover-letter plugin

https://linear.app/agent-layer/issue/AGL-15/build-a-portable-resume-and-cover-letter-plugin · Priority: none · Labels: Spec Kit, High Effort, Complex, Feature · Status at planning: In Progress (claimed for the spec)
Acceptance criteria (from the ticket — plain bullets, NOT checkboxes):

- AC1: A standalone public repository contains shared skills, OpenAI and Claude packaging, sanitized examples/templates, setup docs, a license, and no applicant data.
- AC2: A documented, versioned profile schema and provider contract support structured Markdown and Basic Memory, including precedence, deduplication, provenance, privacy, and approved writes.
- AC3: The four flows are resumable, ask only material questions, and leave one authoritative applicant profile rather than competing copies.
- AC4: Resume and cover-letter generation produce a role brief, requirement-to-evidence map, content plan, and output in the applicant's approved voice and template without inventing qualifications.
- AC5: Editable documents and PDFs pass factual, link/date, text-extraction, pagination, and rendered-layout checks; each output records its source IDs, role brief, template, and version, and representative flows pass on both platform packages.
  Notes from the spec session: the design of record is `specs/20260907-182632-career-documents-plugin/` (spec, plan, research, data model, contracts, quickstart, verification evidence, tasks). Clarifications answered by default and reversible before launch: MIT license; structured Markdown is the default authority with Basic Memory selectable as authoritative; DOCX templates with a sidecar manifest; PDF via local LibreOffice, else the platform's document tools; exactly two positioning modes (executive, builder). "Representative flows pass on both platform packages" is verified structurally by the inventory and installer tests and by the manual-acceptance guidance in the spec's quickstart; the acceptance phase runs those flows.

### AGL-16 — Migrate and organize the resume workspace

https://linear.app/agent-layer/issue/AGL-16/migrate-and-organize-the-resume-workspace · Priority: none · Labels: Med Effort, Regular, Improvement · Parent: AGL-15 · Status at planning: Backlog
Acceptance criteria (from the ticket — plain bullets, NOT checkboxes):

- AC1: An inventory classifies every current file as authoritative data, source evidence, template/voice input, generated output, historical record, duplicate, temporary, or unrelated; nothing is discarded without a recoverable destination.
- AC2: Basic Memory contains the reconciled qualification profile with stable IDs, provenance, verification and visibility metadata, while a validated structured Markdown export provides portability without becoming a competing authority.
- AC3: The current resume design and Brian's voice are captured as reusable, applicant-owned templates/profiles, and `career-documents.json` points to Basic Memory, templates, generated outputs, and workflow state without storing credentials or qualifications.
- AC4: The directory has a documented structure with generated baselines and per-role application bundles separated from source evidence and archive; duplicate PDFs, the temporary ticket draft, and unrelated archive items are removed or relocated recoverably.
- AC5: Fresh executive and builder resume baselines are generated from the migrated setup and pass factual, date/link, text-extraction, two-page, and rendered-layout checks before previous current-state artifacts are archived.
  Notes: depends on AGL-15's schema, providers, checks, and skills, so it runs last. The confirmed facts that must survive the migration are listed in the ticket's description and deliberately not copied into this public repository. Launch preconditions: the workspace copy at `$HOME/development/career-workspace`, LibreOffice on PATH for the PDF checks, and the operator's pre-authorization of the migration diff (recorded on the ticket for review). The acceptance phase should inspect the workspace, the Basic Memory notes, and the baseline output records rather than the repository alone.
