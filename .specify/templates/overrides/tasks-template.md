---
description: "Task list template for feature implementation (career-documents override)"
---

# Tasks: [FEATURE NAME]

**Input**: Design documents from `/specs/[###-feature-name]/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Only generate standalone test tasks when the feature specification explicitly requests them; otherwise include required test work inside the relevant implementation task.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story?] [risky?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2); omit for Setup, Foundational, and Polish tasks
- **[risky]**: Mandatory tag when the task's own diff touches an integration-sensitive surface (see below). The Ralph executor runs `./scripts/gate.sh full` before committing a `[risky]` task and `./scripts/gate.sh basic` otherwise.
- Include exact file paths in descriptions
- **Description** is a single commit-sized deliverable, including required tests and implementation, NOT a single red-or-green TDD step

<!--
  ============================================================================
  GRANULARITY DIRECTIVE (MANDATORY)
  ============================================================================
  Each task MUST be a commit-sized unit a senior engineer completes in one
  sitting: roughly 100–500 lines of diff including tests, at most 3 source
  files named (their tests are implicit), ONE commit. A phase holds 3–10
  tasks. Do NOT emit red/green pairs (test task + implementation task); the
  red→green cycle happens inside one task. Do NOT emit multi-verb tasks
  ("update A and B and C"): split on every "and" boundary so each piece is
  independently gate-able and commit-able. Group by module / surface / file.
  ============================================================================
-->

<!--
  ============================================================================
  AUTONOMOUS EXECUTION CONSTRAINT (MANDATORY)
  ============================================================================
  Every task MUST be completable by an implementation agent without a human:
  no manual inspection or sign-off, no third-party accounts, secrets, OAuth
  apps, or cloud resources, no exploratory QA, no product or business
  decisions not already in spec.md / plan.md / research.md. Manual acceptance
  guidance is a non-task artifact (quickstart.md or checklists/); a task MAY
  create or update that guidance, but the manual check itself is never a task.
  Anything that cannot be done with repository changes, deterministic scripts,
  fixtures, documented environment variables, or automated gates MUST NOT be
  emitted as a task.
  ============================================================================
-->

<!--
  ============================================================================
  RISKY-TASK TAGGING (MANDATORY)
  ============================================================================
  DEFAULT TO BASIC. Tag `[risky]` only when the task's OWN diff creates or
  modifies one of these surfaces:
    1. A skill's SKILL.md frontmatter or its routing to other skills/scripts
       under `skills/` — every platform package consumes it.
    2. A schema under `skills/career-documents/assets/schemas/` or a provider
       contract module — every provider, fixture, and check depends on them.
    3. Package manifests or installers (`.claude-plugin/`, `.agents/`,
       `packages/`), which decide what each platform loads.
    4. `scripts/gate.sh`, `.ralph/command-policy`, `pyproject.toml`, or the
       CI workflow — they alter the bar itself.
    5. The document rendering or checking pipeline entry points that every
       generated output flows through.
  Pure helpers, unit tests, docs, and changes confined to one already-wired
  module's internals are NOT risky. Every user-story phase ends with a
  mandatory `[risky]` verification task; that phase-end gate is the
  integration backstop, so per-task tagging only moves discovery earlier.
  ============================================================================
-->

<!--
  ============================================================================
  PHASE INDEPENDENCE CONSTRAINT (MANDATORY)
  ============================================================================
  Each phase MUST leave HEAD in a state where its own gate passes: basic when
  the phase has no `[risky]` task, full when it has any. A phase whose
  completeness can only be judged together with the next phase is half a
  phase — merge it with its neighbor or reorder so the wiring lands inside
  the phase as its final `[risky]` task. Phase size stays 3–10 tasks.
  ============================================================================
-->

<!--
  ============================================================================
  VERIFICATION TASK REQUIREMENT (MANDATORY)
  ============================================================================
  Every user-story phase MUST end with a `[risky]` verification task that
  exercises the integrated behavior end-to-end through the real data path
  (script invocation → files/provider → observable output), derived from the
  spec's acceptance scenarios and translated into concrete assertions. A test
  that mocks the provider or the renderer does NOT count. If the layer has no
  test infrastructure yet, the phase's first task adds it.

  Immediately BEFORE that verification task, every user-story phase MUST
  include a task that updates `specs/<feature>/verification-evidence.md` with
  the story's outcome map (scenario → method → evidence → status).

  The final polish phase MUST include a task that runs the
  verification-evidence guard (`python3 scripts/verification_evidence_check.py`)
  and confirms zero traceability gaps, and a `[risky]` task that confirms
  `./scripts/gate.sh final` is green.
  ============================================================================
-->

## Path Conventions

- Provider-neutral source: `skills/<skill-name>/` (SKILL.md, scripts/, references/, assets/)
- Schemas: `skills/career-documents/assets/schemas/`; repository tooling: `scripts/`; tests: `tests/unit/`, `tests/integration/`, `tests/fixtures/`
- Platform packages: `.claude-plugin/` (Claude Code/Cowork), `.agents/skills/` and `packages/openai/` (ChatGPT/Codex)
- Sanitized examples: `examples/`; documentation: `docs/`

<!--
  The phases below are SAMPLES. Replace them with real tasks derived from
  spec.md user stories, plan.md, data-model.md, and contracts/. Keep the
  phase shape: Setup → Foundational → one phase per user story (priority
  order) → Polish.
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan
- [ ] T002 [risky] Initialize tooling (`pyproject.toml`, `scripts/gate.sh`) and the test layout

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T003 [risky] Schemas and contract modules every story depends on

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - [Title] (Priority: P1) 🎯 MVP

**Goal**: [Brief description of what this story delivers]

**Independent Test**: [How to verify this story works on its own]

### Implementation for User Story 1

- [ ] T004 [US1] Implement [module] in [path] with its unit tests
- [ ] T005 [US1] Update `specs/<feature>/verification-evidence.md` with the US1 outcome map, automated guard evidence, and generated artifact links.
- [ ] T006 [US1] [risky] Verify US1: [end-to-end assertion derived from the spec's acceptance scenarios]. Test exercises the real data path, not mocked dependencies.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] TXXX Documentation updates in docs/
- [ ] TXXX Run `python3 scripts/verification_evidence_check.py` and resolve every traceability gap
- [ ] TXXX [risky] Verify `./scripts/gate.sh final` passes; if any guard fired, fix the underlying issue (no bypass)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion, then proceed in priority order
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### Within Each User Story

- Models before services; services before flows; core implementation before integration
- Verification-evidence update, then the verification task, always LAST in the phase
- Verification task must PASS before the phase is considered complete

## Implementation Strategy

1. Complete Setup + Foundational → foundation ready
2. Add User Story 1 → verify independently (MVP)
3. Add each further story in priority order → verify independently
4. Polish → final gate green
