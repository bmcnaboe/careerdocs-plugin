# Developing careerdocs

How the plugin is laid out, tested, versioned, and released. Working conventions for
coding agents are in `AGENTS.md`.

## Layout

The repository root is the plugin root, so **every tracked file ships** in every install.

| Path | Purpose |
| --- | --- |
| `skills/careerdocs/` | the core skill: conventions (`SKILL.md`), the CLI reference (`references/cli.md`), the JSON Schemas (`assets/schemas/`), and the CLI (`scripts/careerdocs.py`, package `scripts/careerdocs/`) |
| `skills/onboard/`, `skills/update/`, `skills/apply/` | the user-facing flows, one `SKILL.md` each |
| `skills/*/agents/openai.yaml` | the Codex display name per skill |
| `.claude-plugin/`, `.codex-plugin/`, `.agents/plugins/` | the Claude Code, Cowork, and Codex manifests (`.agents` links to `.claude`) |
| `install.sh` | the one-line installer |
| `examples/applicant/` | a fictional applicant: sources, templates, voice, identity, a posting |
| `tests/unit/`, `tests/integration/` | pytest suites; `tests/fixtures/` holds the extracted candidates and a rendered PDF |
| `scripts/` | the gate and its checks |
| `docs/` | end-user guides linked from the README |

The CLI is deterministic and offline. Skills call it by path; judgement happens between
commands in the conversation. Keep that boundary: anything mechanical (parsing, merging,
selecting, rendering, checking) belongs in the CLI, and the skills stay short.

## Setup

```bash
uv sync --extra dev
```

The `dev` extra installs the CLI's runtime libraries plus pytest and the fixture tooling.
The CLI itself declares its dependencies inline (PEP 723) so it runs standalone under
`uv run` after a skills-only install. LibreOffice (`soffice`) is optional; the tests that
need it pass either way, and the PDF checks report as skipped without it.

## The quality gate

```bash
./scripts/gate.sh [basic|full|final] [--strict]
```

| Tier | Runs |
| --- | --- |
| `basic` (default) | unit tests, skills lint |
| `full` | basic, integration tests, package inventory, version agreement |
| `final` | full, shellcheck, gitleaks, the applicant-data guard, agent-layer conformance |

A component whose tool is missing reports `SKIP`; `--strict` turns that into a failure.
`final --strict` must be green before a commit lands on `main`; CI runs the same tier on
every push. The individual checks are plain scripts: `scripts/lint_skills.py`,
`scripts/check_inventory.py`, `scripts/check_versions.py`, `scripts/pii_guard.py`.

## Tests

Unit tests cover each module; integration tests drive the real CLI end to end over the
example applicant (onboard, résumé, cover letter, update, packaging). Run one file with
`uv run --extra dev python -m pytest tests/unit/test_render.py -q`.

The binary fixtures (the example résumés, the two templates, the rendered PDF) are built
deterministically by `scripts/build_fixtures.py`; rebuild them with
`uv run --extra dev python scripts/build_fixtures.py` after changing the default design
(`--templates-only` rebuilds just the templates).

## Rules that the gate enforces

- **No applicant data, ever.** Everything under `examples/` and `tests/fixtures/` is
  fictional (`example.com` addresses, `555` numbers). `pii_guard.py` scans the rest of the
  tree.
- **Skills lint.** `name` matches the folder, `description` is under 1024 characters,
  frontmatter values avoid `: ` and ` #` unless quoted, the body is under 500 lines.
- **Package inventory.** The Claude and Codex manifests describe the same plugin and load
  the same `skills/`; no developer-local `.mcp.json` is tracked.
- **One version everywhere.** `pyproject.toml` is the version of record; every
  `SKILL.md` `metadata.version`, every manifest, and the CLI's `__version__` must agree.

## Writing skills

Less is more. Each skill is one `SKILL.md`: what the flow does, the steps with the
commands they call, and the guardrails. Put command detail and file shapes in the core
skill's `references/cli.md` rather than restating them, and put rules the CLI can enforce
into the CLI. A new rule earns its place only when a real failure showed it was missing.

## Releasing

1. Bump the version in `pyproject.toml`, `.claude-plugin/plugin.json`,
   `.claude-plugin/marketplace.json`, `.codex-plugin/plugin.json`,
   `skills/careerdocs/scripts/careerdocs/__init__.py`, and each `SKILL.md`;
   `scripts/check_versions.py` confirms they agree.
2. Run `./scripts/gate.sh final --strict`.
3. Commit with a Conventional Commit message and push `main`.
4. Tag `vX.Y.Z` and push the tag. The release workflow runs the gate, builds one zip per
   skill for claude.ai and ChatGPT uploads, and publishes a GitHub Release.

Installs update from `main` (`claude plugin update careerdocs@careerdocs-plugin`,
`codex plugin marketplace upgrade careerdocs-plugin && codex plugin add
careerdocs@careerdocs-plugin`), so a pushed commit is live for anyone who updates; the
tag is what the web-upload zips and the version history hang off.
