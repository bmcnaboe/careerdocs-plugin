---
description: Run speckit-specify, speckit-clarify, then speckit-plan, speckit-tasks, and speckit-analyze in one flow
argument-hint: "[spec-name] feature description or planning guidance"
---

Run the following skills **in sequence**, passing `$ARGUMENTS` to each. This command has two phases; Phase 1 pauses for your input during clarification, then Phase 2 runs automatically once clarification finishes.

## Phase 1 — Specify & Clarify

1. Invoke the `speckit-specify` skill with `$ARGUMENTS`.
2. Once specify completes, invoke the `speckit-clarify` skill with `$ARGUMENTS`. Be sure that each clarify question includes a clear explanation of the context and a clear, crisp phrasing of the question.

**Pause here.** Allow the full interactive `speckit-clarify` loop to run. Do **not** start Phase 2 until clarify is fully finished.

When Phase 1 completes, announce that Phase 2 is starting automatically.

## Phase 2 — Plan, Tasks & Analyze

3. Invoke the `speckit-plan` skill with `$ARGUMENTS`.
4. Once plan completes, invoke the `speckit-tasks` skill with `$ARGUMENTS`.
5. Once tasks completes, invoke the `speckit-analyze` skill with `$ARGUMENTS` **plus** the following additional guidance: "Resolve ALL identified issues autonomously, to the best of your ability. Only raise concerns to me that you absolutely can't resolve on your own with high confidence."

Do not skip or reorder steps within either phase. Wait for each skill to fully complete before invoking the next. Do not require a separate command to continue from Phase 1 to Phase 2.
