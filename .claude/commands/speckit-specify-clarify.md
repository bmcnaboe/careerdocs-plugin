---
description: Run speckit-specify then speckit-clarify in sequence
argument-hint: "[spec-name] feature description"
---

Run the following skills **in sequence**, passing `$ARGUMENTS` to each:

1. Invoke the `speckit-specify` skill with `$ARGUMENTS`.
2. Once specify completes, invoke the `speckit-clarify` skill with `$ARGUMENTS`. Be sure that each of the clarify questions includes a clear explanation of the context, and a clear and crisp phrasing of the question.

Do not skip or reorder steps. Wait for each skill to fully complete before invoking the next.
