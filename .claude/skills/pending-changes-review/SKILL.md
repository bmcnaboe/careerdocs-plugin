---
name: pending-changes-review
description: Review pending git changes for effectiveness, project adherence, architecture, and best practices. Use when the user asks to review changes, assess a diff, or evaluate pending work before commit or PR.
---

# Pending Changes Review

Review staged and unstaged changes, then provide a structured assessment and prioritized recommendations.

## Workflow

1. **Gather context**: Run `git status` and `git diff` (include `--staged` for staged changes)
2. **Read project standards**: Consult [AGENTS.md](../../AGENTS.md), [docs/development/conventions.md](../../docs/development/conventions.md), and [project-conventions skill](../../.claude/skills/project-conventions/SKILL.md) for project-specific criteria
3. **Assess** against the criteria below
4. **Output** using the template in "Output Format"

## Assessment Criteria

### 1. Effectiveness in Achieving Intent

- Does the change accomplish the stated or inferred goal?
- Are there gaps, overreach, or unintended side effects?
- Is the solution minimal and focused?

### 2. Project Standards and Norms

Reference project docs; key checks:

| Area                | Standards                                                                                              |
| ------------------- | ------------------------------------------------------------------------------------------------------ |
| **Architecture**    | Apps in `apps/`, shared in `packages/`; no cross-app imports                                           |
| **File extensions** | `.ts`, `.mts`, `.cts`, `.mjs`, `.cjs` — never `.js`                                                    |
| **Scripts**         | `<component>:<operation>` in `project.json`; no scripts in app `package.json`                          |
| **Testing**         | 100% unit coverage; tests in `tests/unit/`; BDD structure (`describe`/`when`/`should`); mock externals |
| **Code quality**    | Encapsulation, separation of concerns, DRY; remove dead code                                           |
| **Documentation**   | Update docs when architecture, testing, or conventions change                                          |

### 3. Architectural Soundness

- Correct layering (domain, application, persistence, controller)
- Dependencies flow inward (no domain depending on infrastructure)
- Shared logic in `packages/`; no circular dependencies
- Single version policy for dependencies

### 4. Industry Best Practices

- Type safety and appropriate error handling
- Security (no secrets, safe input handling)
- Performance (no obvious N+1, unnecessary work)
- Accessibility (keyboard, focus, semantics) for UI changes
- Test quality: behavior over implementation, flexible assertions, no brittle patterns

## Output Format

Use this structure:

```markdown
## Assessment

### Effectiveness

[1–2 sentences on whether the change achieves its intent and any gaps or overreach]

### Project Adherence

[1–2 sentences on alignment with conventions, architecture, testing, and docs]

### Architecture

[1–2 sentences on layering, dependencies, and structure]

### Best Practices

[1–2 sentences on type safety, security, performance, accessibility, tests]

---

## Recommended Changes

### Critical

[Must fix before merge — correctness, security, architecture violations]

### High

[Should fix — project standards, coverage gaps, maintainability]

### Medium

[Consider — clarity, minor convention drift, small improvements]

### Low

[Nice to have — style, optional refactors]
```

If a category has no items, omit it or write "None."

## Importance Guidelines

| Level        | Examples                                                                                            |
| ------------ | --------------------------------------------------------------------------------------------------- |
| **Critical** | Logic bugs, security issues, cross-app imports, missing tests for new code paths, broken builds     |
| **High**     | Convention violations (file extensions, script format), coverage below 100%, missing error handling |
| **Medium**   | Verbose code, inconsistent naming, minor test brittleness                                           |
| **Low**      | Style tweaks, optional refactors, documentation polish                                              |
