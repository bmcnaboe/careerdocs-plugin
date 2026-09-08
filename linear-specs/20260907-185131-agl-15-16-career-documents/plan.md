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
   The design of record for AGL-15 sits beside this plan in `design/`: `spec.md`
   (user stories, requirements, success criteria), `implementation-plan.md`
   (technical context, project structure, verification strategy), `research.md`
   (decisions R1–R17), `data-model.md`, `contracts/` (provider, CLI, artifacts,
   packages, schemas), `quickstart.md`, and `verification-evidence.md`. Read the
   ones a task names; the tranche and task order here already encodes the
   implementation plan's phases.
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

- [x] T001 [AGL-15] Claim tranche: post the start comment on AGL-15 naming branch `linear/agl-15-16-career-documents` and this plan; capture the comment's `author.id`; ensure AGL-15 is In Progress with that assignee (it may already be, then only the comment is new).
- [x] T002 [AGL-15] [risky] Create `pyproject.toml` (name `career-documents`, version `0.1.0`, `requires-python >= 3.11`, `[project.optional-dependencies] dev` = pytest, jsonschema, docxtpl, python-docx, pypdf, pdfplumber, pypdfium2, python-dateutil, reportlab), run `uv sync --extra dev` and commit `uv.lock`, and add `tests/unit/test_pyproject.py` asserting the file parses with `tomllib` and carries the version, so `./scripts/gate.sh basic` runs the unit suite for real
- [x] T003 [AGL-15] Add `LICENSE` (MIT), `README.md` (what the plugin is, the four flows, the four authorities, the no-applicant-data rule, install pointers to `docs/`), and `docs/README.md` as the documentation index
- [x] T004 [AGL-15] Implement `scripts/pii_guard.py` (standard library; scans `git ls-files` outside `examples/` and `tests/fixtures/` for email addresses not on `example.com`/`example.org`, telephone numbers not using `555`, and street-address patterns; prints `file:line: pattern`; exit 1 on findings) with `tests/unit/test_pii_guard.py`
- [x] T005 [AGL-15] Implement `scripts/lint_skills.py` (standard library flat-YAML frontmatter parser; enforces the Agent Skills rules: `name` matches the directory, 1–64 chars, lowercase/digits/hyphens, no leading, trailing, or double hyphens; `description` 1–1024 chars; `compatibility` ≤ 500; `metadata` string map; body ≤ 500 lines; `agents/openai.yaml` when present is a flat key-value file) with `tests/unit/test_lint_skills.py`
- [x] T006 [AGL-15] Implement `scripts/verification_evidence_check.py` (parses acceptance scenarios from `design/spec.md` per user story and the rows of `design/verification-evidence.md` under `linear-specs/20260907-185131-agl-15-16-career-documents/`; fails on a scenario without a row or a row without evidence; `--require-complete` additionally fails on any `pending`) with `tests/unit/test_verification_evidence_check.py`
- [x] T007 [AGL-15] Implement `scripts/check_versions.py` (reads the version of record from `pyproject.toml`; requires every `skills/*/SKILL.md` `metadata.version` to equal it; compares `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, and `packages/openai/manifest.json` when present and reports which manifests are absent) with `tests/unit/test_check_versions.py`
- [x] T008 [AGL-15] [risky] Add `.github/workflows/ci.yml` (ubuntu-latest; checkout; `astral-sh/setup-uv`; `uv sync --extra dev`; install shellcheck and gitleaks; run `./scripts/gate.sh final`) so every push and pull request runs the full bar
- [x] T009 [AGL-15] [risky] Create `skills/career-documents/SKILL.md` (core conventions: the four authorities and where each lives, how flow skills invoke `careerdocs`, the diff-then-approve rule, visibility semantics, where state and outputs go), `skills/career-documents/agents/openai.yaml`, `skills/career-documents/assets/schemas/career-profile.schema.json` and `config.schema.json` (copied from `linear-specs/20260907-185131-agl-15-16-career-documents/design/contracts/`), and `skills/career-documents/references/schema.md`
- [x] T010 [AGL-15] Create `skills/career-documents/scripts/careerdocs.py` (PEP 723 header declaring docxtpl, pypdf, pdfplumber, pypdfium2, jsonschema, python-dateutil; delegates to `careerdocs.cli:main`) and `skills/career-documents/scripts/careerdocs/cli.py` (argparse with `--workspace`, `--json`, exit codes 0/1/2, `version`, a minimal `doctor`) with `tests/unit/test_cli.py`
- [x] T011 [AGL-15] Implement `skills/career-documents/scripts/careerdocs/config.py` (defaults for every key, load and validate against `config.schema.json`, refusal of credential-like or qualification-like keys, `config init` and `config validate` subcommands) with `tests/unit/test_config.py`
- [x] T012 [AGL-15] Implement `skills/career-documents/scripts/careerdocs/ids.py` (ULID generation and `<type>_<ULID>` parsing) and `skills/career-documents/scripts/careerdocs/schema.py` (jsonschema validation plus semantic rules: date order, no future dates, reference resolution, single contact, unresolved conflicts block their field) with `tests/unit/test_schema.py`
- [x] T013 [AGL-15] [risky] Implement `skills/career-documents/scripts/careerdocs/providers/base.py` (the provider interface and typed errors from the provider contract) and `skills/career-documents/scripts/careerdocs/providers/markdown.py` (index and per-entity files, `sources.jsonl`, `approvals.jsonl`, `diffs/`, canonical hash, read, export) with `tests/unit/test_markdown_provider.py`
- [x] T014 [AGL-15] Implement `skills/career-documents/scripts/careerdocs/providers/basic_memory.py` (per-entity Basic Memory notes with the schema fields in frontmatter, `## Observations` and `## Relations` sections, `<folder>/<type>/<id>` permalinks; read back; export to the Markdown layout with `derived: true`) with `tests/unit/test_basic_memory_provider.py`
- [x] T015 [AGL-15] Implement `skills/career-documents/scripts/careerdocs/diff.py` (ProfileDiff operations, `base_hash`, Markdown rendering, `profile diff`, `profile approve` writing hash-bound approvals, `profile apply` refusing on missing approval or base-hash mismatch and refreshing derived exports, `profile validate`, `profile export`) with `tests/unit/test_diff.py`
- [x] T016 [AGL-15] Implement `skills/career-documents/scripts/careerdocs/state.py` (WorkflowState per flow and subject, append-only questions that are never asked twice, `state show`, `state answer`, `state resume`) with `tests/unit/test_state.py`
- [x] T017 [AGL-15] Create the fictional example applicant: `scripts/build_fixtures.py` (deterministic; builds `examples/applicant/sources/resume-a.docx` with python-docx and `resume-b.pdf` with reportlab, the two disagreeing on one end date) plus the committed `examples/applicant/career-documents.json`, `voice/voice.md`, `sources/network-export.csv`, `sources/voice-note.md`, `applications/example-role/job-description.md` (with one requirement the profile cannot meet), and `tests/fixtures/candidates.json` (the extracted candidate set containing the deliberate conflict)
- [x] T018 [AGL-15] [risky] Close tranche A: full gate green; comment on AGL-15 summarizing what landed (commits, surfaces); AGL-15 stays In Progress

### Tranche B — Packages and onboarding (AGL-15)

- [x] T019 [AGL-15] [risky] Create `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` (single plugin, `source: "./"`) and implement `scripts/check_inventory.py` (skills tree versus the Claude manifest; runs `claude plugin validate .` when the CLI is on PATH) with `tests/unit/test_check_inventory.py`
- [x] T020 [AGL-15] [risky] Create `packages/openai/manifest.json` and `packages/openai/install.py` (standard library; `--link` default, `--copy`, `--home`, `--dry-run`, `--uninstall`; targets `$HOME/.agents/skills/`; prints the ChatGPT skill-upload steps; exits non-zero when the manifest disagrees with `skills/`) with `tests/unit/test_install.py`; extend `scripts/check_inventory.py` to compare the OpenAI manifest and `scripts/check_versions.py` to require both manifests
- [x] T021 [AGL-15] Write `docs/setup-claude.md` (marketplace add, plugin install, Cowork note, verification via `claude plugin details`) and `docs/setup-codex.md` (installer usage, ChatGPT upload, verification via `ls ~/.agents/skills`), and the README install section
- [x] T022 [AGL-15] Update `linear-specs/20260907-185131-agl-15-16-career-documents/design/verification-evidence.md` with the US1 outcome map, automated guard evidence, and generated artifact links
- [ ] T023 [AGL-15] [risky] Verify US1: `tests/integration/test_packages.py` builds the inventory from `skills/` and both manifests and asserts zero differences, runs `packages/openai/install.py --link --home <tmp>` and asserts every installed `SKILL.md` is byte-identical to its source and that the install contains no applicant data, runs `scripts/pii_guard.py` over tracked files asserting zero findings, and runs `claude plugin validate .` when available. Test exercises the real files, not mocked manifests.
- [ ] T024 [AGL-15] Implement `skills/career-documents/scripts/careerdocs/importers/` (`docx.py`, `pdf.py`, `network_export.py`, `note.py`) and `profile import` (registers sources with sha256 in `sources.jsonl`, emits text blocks and candidate skeletons as JSON) with `tests/unit/test_importers.py` over `examples/applicant/sources/`
- [ ] T025 [AGL-15] Implement `skills/career-documents/scripts/careerdocs/merge.py` (candidates → deduplication keys per type, precedence order, conflict candidates → ProfileDiff via `profile diff`) with `tests/unit/test_merge.py` asserting the two disagreeing résumés yield one experience with both provenance entries and exactly one conflict
- [ ] T026 [AGL-15] Implement `skills/career-documents/scripts/careerdocs/questions.py` (materiality rules; questions generated from conflicts, missing dates, and visibility defaults; persisted through `state.py`; answers become `resolve_conflict` or `update_field` operations) with `tests/unit/test_questions.py` asserting no question repeats after a resume
- [ ] T027 [AGL-15] Implement visibility filtering (`visible_for(document)` in the providers and exports, `restricted` per-document approvals via `profile approve --document`, `derived: true` labeling on every export) with `tests/unit/test_visibility.py`
- [ ] T028 [AGL-15] [risky] Create `skills/career-onboard/SKILL.md`, `skills/career-onboard/agents/openai.yaml`, and `skills/career-onboard/references/playbook.md` (inventory sources → `profile import` → extract candidates into `candidates.json` against the schema → `profile diff` → ask only the generated questions → `profile approve` after an explicit yes → `profile apply` → `profile export`), and add the skill to both package manifests
- [ ] T029 [AGL-15] Update `linear-specs/20260907-185131-agl-15-16-career-documents/design/verification-evidence.md` with the US2 outcome map, automated guard evidence, and generated artifact links
- [ ] T030 [AGL-15] [risky] Verify US2: `tests/integration/test_onboard.py` runs import → diff → one question → answer → approve → apply → export on the example sources and asserts one role entry with both provenance entries and `applicant_verified`, resumes an interrupted run without repeating the question, and confirms a private fact is absent from the export; `tests/integration/test_basic_memory_provider.py` repeats the sequence with `authoritative: basic_memory` in a temporary vault and asserts the same IDs in the notes and a `derived: true` Markdown export. Tests exercise the real CLI and files, not mocked providers.
- [ ] T031 [AGL-15] [risky] Close tranche B: full gate green; progress comment on AGL-15

### Tranche C — Tailored résumé (AGL-15)

- [ ] T032 [AGL-15] Implement `skills/career-documents/scripts/careerdocs/brief.py` (`brief`: job description from file or URL text; requirement skeletons with stable ids and must/nice kind; keyword extraction; positioning recommendation; validation of the agent-completed brief) and `skills/career-documents/assets/schemas/role-brief.schema.json` with `tests/unit/test_brief.py`
- [ ] T033 [AGL-15] Implement `skills/career-documents/scripts/careerdocs/mapping.py` (`map`: candidate evidence per requirement by keyword and skill overlap; validation that every requirement appears exactly once, `gap` entries have no evidence, classifications are valid) and `skills/career-documents/assets/schemas/requirement-map.schema.json` with `tests/unit/test_mapping.py`
- [ ] T034 [AGL-15] Implement `skills/career-documents/scripts/careerdocs/plan.py` (`plan`: selection, ordering, and emphasis by positioning tags; page-budget estimate from the template manifest; cut list; units carrying `source_ids`; template allowlist) and `skills/career-documents/assets/schemas/content-plan.schema.json` with `tests/unit/test_plan.py` (`test_positioning_inverts`, `test_budget_cuts_reported`)
- [ ] T035 [AGL-15] [risky] Implement `skills/career-documents/scripts/careerdocs/render.py` (`render`: docxtpl rendering from the content plan and voice profile into the template; timestamped output naming; output-record skeleton; `--pdf` via `soffice` when present, reported when absent) and the example résumé template `examples/applicant/templates/resume/template.docx` + `template.json` built by `scripts/build_fixtures.py`, with `tests/unit/test_render.py`
- [ ] T036 [AGL-15] Implement `skills/career-documents/scripts/careerdocs/checks/factual.py` (unit matching, token traceability of numbers, dates, organizations, and titles to cited entities, template allowlist) and `skills/career-documents/scripts/careerdocs/checks/links_dates.py` (date parsing, ordering, no future dates; link syntax; optional network check recorded as `skipped` offline) with `tests/unit/test_checks_factual.py`
- [ ] T037 [AGL-15] Implement `skills/career-documents/scripts/careerdocs/checks/extraction.py`, `pagination.py`, and `layout.py` (pypdf text extraction; page count against the budget; pdfplumber margin and density heuristics; pypdfium2 page PNGs) with the committed fixture `tests/fixtures/rendered/example-resume.pdf` and `tests/unit/test_checks_layout.py`
- [ ] T038 [AGL-15] Implement `skills/career-documents/scripts/careerdocs/record.py` (`check`: runs the five checks, writes the OutputRecord, exit codes) and `skills/career-documents/assets/schemas/output-record.schema.json` with `tests/unit/test_record.py`
- [ ] T039 [AGL-15] [risky] Create `skills/career-resume/SKILL.md`, `skills/career-resume/agents/openai.yaml`, and `skills/career-resume/references/playbook.md` (brief → complete requirements → map with direct/transferable/gap judgement → choose positioning → plan → draft units in voice → render → check → report cuts and gaps), and add the skill to both package manifests
- [ ] T040 [AGL-15] Update `linear-specs/20260907-185131-agl-15-16-career-documents/design/verification-evidence.md` with the US3 outcome map, automated guard evidence, and generated artifact links
- [ ] T041 [AGL-15] [risky] Verify US3: `tests/integration/test_resume.py` runs brief → map → plan → render → check on the example job description and asserts the four artifacts exist in order, the unmet requirement is a `gap` and no rendered sentence claims it, switching positioning inverts emphasis without changing any fact, all five checks report `pass` (link check `pass` or `skipped` offline), and page-budget cuts are reported. Test exercises the real CLI, template, and rendered files, not mocked dependencies.
- [ ] T042 [AGL-15] [risky] Close tranche C: full gate green; progress comment on AGL-15

### Tranche D — Cover letter, updates, polish (AGL-15)

- [ ] T043 [AGL-15] Extend `skills/career-documents/scripts/careerdocs/plan.py` with `--kind cover_letter` (paragraph units, top requirements by value, gap policy, exclusion of verbatim résumé bullets, letter page budget) with additions to `tests/unit/test_plan.py`
- [ ] T044 [AGL-15] Add the example letter template `examples/applicant/templates/cover-letter/template.docx` + `template.json` to `scripts/build_fixtures.py`, support `render --kind cover_letter`, and add the verbatim-bullet check to `skills/career-documents/scripts/careerdocs/checks/factual.py` with additions to `tests/unit/test_render.py` and `tests/unit/test_checks_factual.py`
- [ ] T045 [AGL-15] [risky] Create `skills/career-cover-letter/SKILL.md`, `skills/career-cover-letter/agents/openai.yaml`, and `skills/career-cover-letter/references/playbook.md` (reuse brief and map without re-asking; draft in voice; complement, do not repeat; handle gaps honestly), and add the skill to both package manifests
- [ ] T046 [AGL-15] Update `linear-specs/20260907-185131-agl-15-16-career-documents/design/verification-evidence.md` with the US4 outcome map, automated guard evidence, and generated artifact links
- [ ] T047 [AGL-15] [risky] Verify US4: `tests/integration/test_cover_letter.py` generates the letter for the example role after the résumé and asserts the brief and map are reused with zero new questions, every claim traces to a profile ID, the gap requirement is not claimed, the letter fits its page budget, and no résumé bullet appears verbatim. Test exercises the real CLI and rendered files.
- [ ] T048 [AGL-15] Extend `profile apply` in `skills/career-documents/scripts/careerdocs/diff.py` to mark output records whose `source_ids` include a changed entity as stale (with reason) and implement `profile status` (stale outputs, derived export freshness) with additions to `tests/unit/test_diff.py`
- [ ] T049 [AGL-15] [risky] Create `skills/career-update/SKILL.md`, `skills/career-update/agents/openai.yaml`, and `skills/career-update/references/playbook.md` (capture the statement with provenance → candidates → `profile diff` → approve → apply → report stale outputs; resume from pending diff), and add the skill to both package manifests
- [ ] T050 [AGL-15] Update `linear-specs/20260907-185131-agl-15-16-career-documents/design/verification-evidence.md` with the US5 outcome map, automated guard evidence, and generated artifact links
- [ ] T051 [AGL-15] [risky] Verify US5: `tests/integration/test_update.py` applies an update that changes one end date and adds one achievement, and asserts the new fact carries a fresh ID, statement provenance, and `applicant_verified`, the authoritative profile and the derived export agree, the earlier example résumé's output record is reported stale, and an interrupted update resumes to the same pending diff without re-asking. Test exercises the real CLI and files.
- [ ] T052 [AGL-15] Write `docs/configuration.md`, `docs/profile-schema.md`, and `docs/provider-contract.md` from the contracts and the shipped schemas
- [ ] T053 [AGL-15] Write `docs/checks.md` and `docs/templates-and-voice.md`, and complete `README.md` (flows, platforms, privacy model, links to every document)
- [ ] T054 [AGL-15] Complete `skills/career-documents/references/provider-contract.md`, `references/checks.md`, `references/configuration.md`, and the `doctor` command (converter detection, dependency status, provider reachability, template and voice presence) with additions to `tests/unit/test_cli.py`
- [ ] T055 [AGL-15] Run `python3 scripts/verification_evidence_check.py --require-complete`, resolve every traceability gap in `linear-specs/20260907-185131-agl-15-16-career-documents/design/verification-evidence.md`, and finalize the manual-acceptance guidance in `linear-specs/20260907-185131-agl-15-16-career-documents/design/quickstart.md`
- [ ] T056 [AGL-15] [risky] Switch `.github/workflows/ci.yml` to `./scripts/gate.sh final --strict` and remove every remaining `SKIP` by adding the missing component, never by loosening the gate
- [ ] T057 [AGL-15] [risky] Close tranche D: `./scripts/gate.sh final --strict` green; comment on AGL-15 summarizing what landed and how to verify it, and move AGL-15 to In Review

### Tranche E — Migrate the applicant workspace (AGL-16)

- [ ] T058 [AGL-16] Claim tranche: confirm the workspace copy exists per the Tranche E rules (GUTTER if not); post the start comment on AGL-16 naming the branch and this plan; move AGL-16 to In Progress with the comment author as assignee
- [ ] T059 [AGL-16] Implement `careerdocs inventory <dir>` in `skills/career-documents/scripts/careerdocs/inventory.py` (classifies every file as authoritative data, source evidence, template/voice input, generated output, historical record, duplicate by sha256, temporary, or unrelated; writes `inventory.json` and `inventory.md` with a proposed recoverable destination per file) with `tests/unit/test_inventory.py` on a fixture tree
- [ ] T060 [AGL-16] Implement `careerdocs organize --inventory <file> [--apply|--rollback] [--dry-run]` in `skills/career-documents/scripts/careerdocs/organize.py` (moves files into the documented structure `sources/`, `templates/`, `voice/`, `baselines/`, `applications/`, `archive/`, `.career-documents/`; never deletes; every move recorded in `.career-documents/moves.jsonl`; rollback replays it) with `tests/unit/test_organize.py`
- [ ] T061 [AGL-16] Run `careerdocs inventory` on the workspace, review the classification for sense (résumés are source evidence, `output/` copies are duplicates, the Linear draft is temporary, non-career items under `archive/` are unrelated when that folder is present), save `inventory.md` in the workspace, and post the class counts to AGL-16
- [ ] T062 [AGL-16] Write the workspace `career-documents.json` (Basic Memory authoritative per the Tranche E rules; Markdown export at `profile/`; templates, voice, outputs, and state paths), run `config validate` and `doctor`, and post the doctor summary to AGL-16
- [ ] T063 [AGL-16] Onboard the applicant: `profile import` over `resume_source_of_truth.md` (registered as the applicant statement source), every current and archived résumé, and the LinkedIn export and notes when present (record on the ticket what was absent); extract candidates; `profile diff`; resolve conflicts by precedence and leave the rest open; approve under the launch pre-authorization; `profile apply` (Basic Memory notes plus the derived Markdown export); confirm every confirmed fact from AGL-16's description is present and `applicant_verified`; post the rendered diff and open conflicts to AGL-16
- [ ] T064 [AGL-16] Capture voice and template: draft `voice/voice.md` from the current résumés and, when present in the workspace, `held_sleep_brand_guidelines.md`; convert the current résumé DOCX into `templates/resume/template.docx` + `template.json` (styles kept, content replaced by placeholders, two-page budget) and derive `templates/cover-letter/`; `doctor` reports both present
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
  Notes from the spec session: the design of record is `design/` beside this plan (spec, implementation plan, research, data model, contracts, quickstart, verification evidence). Clarifications answered by default and reversible before launch: MIT license; structured Markdown is the default authority with Basic Memory selectable as authoritative; DOCX templates with a sidecar manifest; PDF via local LibreOffice, else the platform's document tools; exactly two positioning modes (executive, builder). "Representative flows pass on both platform packages" is verified structurally by the inventory and installer tests and by the manual-acceptance guidance in the spec's quickstart; the acceptance phase runs those flows.

### AGL-16 — Migrate and organize the resume workspace

https://linear.app/agent-layer/issue/AGL-16/migrate-and-organize-the-resume-workspace · Priority: none · Labels: Med Effort, Regular, Improvement · Parent: AGL-15 · Status at planning: Backlog
Acceptance criteria (from the ticket — plain bullets, NOT checkboxes):

- AC1: An inventory classifies every current file as authoritative data, source evidence, template/voice input, generated output, historical record, duplicate, temporary, or unrelated; nothing is discarded without a recoverable destination.
- AC2: Basic Memory contains the reconciled qualification profile with stable IDs, provenance, verification and visibility metadata, while a validated structured Markdown export provides portability without becoming a competing authority.
- AC3: The current resume design and Brian's voice are captured as reusable, applicant-owned templates/profiles, and `career-documents.json` points to Basic Memory, templates, generated outputs, and workflow state without storing credentials or qualifications.
- AC4: The directory has a documented structure with generated baselines and per-role application bundles separated from source evidence and archive; duplicate PDFs, the temporary ticket draft, and unrelated archive items are removed or relocated recoverably.
- AC5: Fresh executive and builder resume baselines are generated from the migrated setup and pass factual, date/link, text-extraction, two-page, and rendered-layout checks before previous current-state artifacts are archived.
  Notes: depends on AGL-15's schema, providers, checks, and skills, so it runs last. The confirmed facts that must survive the migration are listed in the ticket's description and deliberately not copied into this public repository. Launch preconditions: the workspace copy at `$HOME/development/career-workspace`, LibreOffice on PATH for the PDF checks, and the operator's pre-authorization of the migration diff (recorded on the ticket for review). The acceptance phase should inspect the workspace, the Basic Memory notes, and the baseline output records rather than the repository alone.
