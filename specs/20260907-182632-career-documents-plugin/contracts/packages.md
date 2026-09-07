# Package Contracts

## Shared source

`skills/<name>/SKILL.md` for `career-documents`, `career-onboard`, `career-update`,
`career-resume`, `career-cover-letter`. Frontmatter per the Agent Skills specification:
`name` (equals the directory), `description`, `license: MIT`, `compatibility` (Python
3.11+, uv recommended), `metadata.version` (equals the plugin version),
`metadata.author`. Optional per-skill `agents/openai.yaml` (display name, short
description, `allow_implicit_invocation`). Scripts live only in
`skills/career-documents/scripts/`; flow skills reference them by relative path.

## Claude Code / Cowork

- `.claude-plugin/plugin.json`: `name: career-documents`, `version`, `description`,
  `author`, `homepage`, `repository`, `license: MIT`, `keywords`. No custom component
  paths; skills are auto-discovered from `skills/`.
- `.claude-plugin/marketplace.json`: `name: career-documents`, `owner`, one plugin entry
  `{ name: career-documents, source: "./", description, version }`.
- Verification: `claude plugin validate .` exits 0; `claude plugin details` (after
  install) lists exactly the five skills.

## ChatGPT / Codex

- `packages/openai/manifest.json`: `name`, `version`, `skills[] { name, description, path }`.
- `packages/openai/install.py`: standard library; `--link` (default, symlinks) or
  `--copy`; target `$HOME/.agents/skills/`; `--uninstall`; prints the ChatGPT skill
  upload instructions; exits non-zero if the manifest disagrees with `skills/`.
- Verification: after install, `ls $HOME/.agents/skills` lists the five skills, and
  each `SKILL.md` is byte-identical to the source.

## Inventory equality (SC-001)

`scripts/check_inventory.py` derives the inventory from `skills/` and compares it with
the Claude manifest (name, version) and the OpenAI manifest (name, description, version)
and fails on any difference. It runs in the full gate.
