---
description: Run speckit-plan, speckit-tasks, then speckit-analyze in sequence
argument-hint: "[spec-name] optional planning guidance"
---

Run the following skills **in sequence**, passing `$ARGUMENTS` to each:

1. Invoke the `speckit-plan` skill with `$ARGUMENTS`.
2. Once plan completes, invoke the `speckit-tasks` skill with `$ARGUMENTS`.
3. Once tasks completes, invoke the `speckit-analyze` skill with `$ARGUMENTS` **plus** the following additional guidance: "Resolve ALL identified issues autonomously, to the best of your ability. Only raise concerns to me that you absolutely can't resolve on your own with high confidence."

Do not skip or reorder steps. Wait for each skill to fully complete before invoking the next.
