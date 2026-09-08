# Setup — Claude Code, the desktop app, claude.ai, and Cowork

The repository *is* the plugin: its `.claude-plugin/` manifests and `skills/` tree are
consumed in place, so installing is adding the repository as a marketplace and installing
the plugin from it. No clone is needed.

## Prerequisites

- Claude Code (CLI, desktop app, or IDE extension).
- Python 3.11+ or [uv](https://docs.astral.sh/uv/) (uv recommended — the `careerdocs`
  CLI declares its dependencies inline and runs under `uv run`).
- Optional: LibreOffice (`soffice` on PATH) for PDF conversion. Without it, editable
  documents still render and the pagination/layout checks report as skipped.

## Install

The one-liner detects Claude Code and runs the two commands below for you (and installs
for Codex too when it finds it):

```sh
curl -fsSL https://raw.githubusercontent.com/bmcnaboe/careerdocs-plugin/main/install.sh | bash
```

By hand, the same two commands:

```sh
claude plugin marketplace add bmcnaboe/careerdocs-plugin
claude plugin install careerdocs-plugin@careerdocs-plugin
```

The two arguments are `<plugin>@<marketplace>`; both are named `careerdocs-plugin`. The
install lands at user scope, so it is available in every project; add `--scope project`
to share it with a repository's collaborators instead. A session that is already open
picks it up after `/reload-plugins`; new sessions load it automatically.

**Desktop app.** Once the marketplace is added (the CLI step above, or the one-liner), the
plugin appears in the desktop plugin browser: click **+** next to the prompt box →
**Plugins** → **Add plugin**. **Manage plugins** in the same menu enables, disables, or
uninstalls it.

**claude.ai and Cowork.** These do not read `~/.claude`; they take skills from your
claude.ai account. Download the per-skill zips from the
[latest release](https://github.com/bmcnaboe/careerdocs-plugin/releases/latest) and add
each one under **Customize → Skills** (one skill per zip; code execution must be enabled
in Settings → Capabilities). The skills then guide the conversation; generating documents
needs an agent that can run the `careerdocs` CLI, so use Claude Code for that.

## Verify

```sh
claude plugin details careerdocs-plugin
```

lists the installed skills — the core `careerdocs` skill plus the flow skills
(`career-onboard`, `career-update`, `career-resume`, `career-cover-letter`). To confirm
the CLI itself, ask Claude Code in the folder that holds your career documents:

> run careerdocs doctor

`doctor` reports your configuration, provider, template, voice, converter, and dependency
status.

## Update and remove

```sh
claude plugin update careerdocs-plugin@careerdocs-plugin
claude plugin uninstall careerdocs-plugin@careerdocs-plugin
```

Re-running the one-liner also updates; `install.sh --uninstall` removes the plugin and
the marketplace together.
