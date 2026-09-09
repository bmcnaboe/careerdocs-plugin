# Setup — Claude Code, the desktop app, Cowork, and claude.ai

The repository *is* the plugin: its `.claude-plugin/` manifests and `skills/` tree are
consumed in place, so installing is adding the repository as a marketplace and installing
the plugin from it. No clone is needed.

## Prerequisites

- Claude Code (CLI, desktop app, or IDE extension).
- Python 3.10+ or [uv](https://docs.astral.sh/uv/) (uv recommended — the `careerdocs`
  CLI declares its dependencies inline and runs under `uv run`; without uv it installs
  them with pip on first run). Cowork needs nothing installed locally: its sandbox
  already has Python and can reach PyPI.
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
claude plugin install careerdocs@careerdocs-plugin
```

The two arguments are `<plugin>@<marketplace>`: the plugin is `careerdocs`, and the
marketplace is named after the repository, `careerdocs-plugin`. The install lands at user scope, so it is available in every project; add `--scope project`
to share it with a repository's collaborators instead. A session that is already open
picks it up after `/reload-plugins`; new sessions load it automatically.

## Workspace

The skills work in one folder — the **workspace** — that holds your profile, templates,
voice, and generated documents. The one-liner asks for it (default `~/career-workspace`)
and records the choice in `~/.config/careerdocs/workspace`, so every session finds it
whatever folder it starts in. Installing by hand, or from a non-interactive shell, leaves
it unrecorded; set it from a session with

> careerdocs config workspace ~/career-workspace

or re-run the one-liner with `--workspace <dir>`. Per command, `--workspace <dir>`
overrides the recorded default, and a folder that already holds a `careerdocs.json` is
used when a session starts inside it.

**Desktop app.** Once the marketplace is added (the CLI step above, or the one-liner), the
plugin appears in the desktop plugin browser: click **+** next to the prompt box →
**Plugins** → **Add plugin**. **Manage plugins** in the same menu enables, disables, or
uninstalls it.

## Cowork

Cowork keeps its own plugin list, separate from Claude Code's: `claude plugin install` and
the one-liner do not reach it. It reads marketplaces straight from Git, so the install is
three clicks and no terminal:

1. In the desktop app open the **Cowork** tab, then **Customize → Plugins**.
2. Select **Add marketplace** and enter `bmcnaboe/careerdocs-plugin`.
3. Install **careerdocs** from the marketplace that appears, then open it once to confirm
   its five skills are enabled. **Update** on the marketplace pulls new versions later;
   Cowork keeps its own versioned copy, refreshed from GitHub.

Start a **new** session with your workspace folder attached (create one,
`~/career-workspace` say, if you have none), type `/`, and pick `careerdocs:onboard`. If
`/` does not offer it, say "onboard my career documents": the skills trigger on their
descriptions as well. The attached folder *is* the workspace: the skills run the CLI
against it and write `careerdocs.json` there on first use, so nothing needs to be recorded
on your machine. Cowork runs the CLI in its own sandbox, which has Python and reaches
PyPI; the CLI installs its dependencies there on its first run. LibreOffice, needed for
PDF output and the PDF checks, is present in cloud sessions and absent in local ones,
where documents still render and those checks report as skipped.

Team and Enterprise owners can make a marketplace install automatically for every member
under Organization settings → Plugins, but organization marketplaces must be private or
internal repositories, so that route does not apply to this public one.

**claude.ai chat.** Chat does not run plugins; it takes skills from your account. Download
the per-skill zips from the
[latest release](https://github.com/bmcnaboe/careerdocs-plugin/releases/latest) and add
each one under **Customize → Skills** (one skill per zip; code execution must be enabled
in Settings → Capabilities). The skills then guide the conversation; generating documents
needs an agent that can run the `careerdocs` CLI, so use Claude Code or Cowork for that.

## Verify

```sh
claude plugin details careerdocs
```

lists the installed skills — the core `careerdocs` skill plus the flow skills (`onboard`,
`update`, `resume`, `cover-letter`), invoked as `/careerdocs:<skill>`. Start with
`/careerdocs:onboard` to bring your existing materials into one profile, then
`/careerdocs:resume`, `/careerdocs:cover-letter`, and `/careerdocs:update` per
application. To confirm the CLI itself, ask Claude Code in any folder:

> run careerdocs doctor

`doctor` reports the workspace it resolved (and how), your configuration, provider,
template, voice, converter, and dependency status.

## Update and remove

```sh
claude plugin update careerdocs@careerdocs-plugin
claude plugin uninstall careerdocs@careerdocs-plugin
```

Re-running the one-liner also updates; `install.sh --uninstall` removes the plugin, the
marketplace, and the recorded workspace default together (the workspace folder itself is
never touched). An install made when the plugin was still named
`careerdocs-plugin` is replaced by the one-liner; by hand, uninstall
`careerdocs-plugin@careerdocs-plugin` first.
