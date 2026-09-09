# Setup — Codex and ChatGPT

Codex installs plugins from Git marketplaces with its own plugin manager and keeps a
versioned copy under `~/.codex/plugins/cache`. This repository is such a marketplace:
`.agents/plugins/marketplace.json` lists the plugin and `.codex-plugin/plugin.json`
describes it, pointing at the same `skills/` that Claude Code and Cowork load. ChatGPT
takes the same skills as zip uploads.

## Prerequisites

- Codex CLI or app with plugin support (`codex plugin --help` works).
- Python 3.10+ or [uv](https://docs.astral.sh/uv/) (uv recommended for the `careerdocs`
  CLI; under plain `python3` it installs its dependencies with pip on first run).
- Optional: LibreOffice (`soffice` on PATH) for PDF conversion.

## Install for Codex

The one-liner detects Codex and runs the two commands below (and installs for Claude Code
too when it finds it):

```sh
curl -fsSL https://raw.githubusercontent.com/bmcnaboe/careerdocs-plugin/main/install.sh | bash
```

By hand, the same two commands:

```sh
codex plugin marketplace add bmcnaboe/careerdocs-plugin
codex plugin add careerdocs@careerdocs-plugin
```

`bmcnaboe/careerdocs-plugin@v1.2.0` pins a tag. From a local clone, add the clone's path
as the marketplace instead and run the same `codex plugin add`; Codex copies the plugin
into its cache from there. Restart Codex after installing so a session that is already
open discovers the skills.

Earlier versions of the one-liner copied the skills into `~/.agents/skills`. Re-running
it removes those copies; by hand, delete the five skill folders there, or they shadow the
plugin's skills and drift from them.

## Verify

```sh
codex plugin marketplace list      # careerdocs-plugin
codex plugin list                  # careerdocs@careerdocs-plugin  installed, enabled
```

In a session, `/skills` lists the plugin's skills, and `$onboard`, `$resume`,
`$cover-letter`, and `$update` invoke them the same way as any other skill (when a
personal skill shares a name, Codex lists both). Start with `$onboard`. To confirm the
CLI itself, run it from the installed copy:

```sh
uv run ~/.codex/plugins/cache/careerdocs-plugin/careerdocs/*/skills/careerdocs/scripts/careerdocs.py version
```

## Workspace

The skills work in one folder — the **workspace** — that holds your profile, templates,
voice, and generated documents. The one-liner asks for it (default `~/career-workspace`)
and records the choice in `~/.config/careerdocs/workspace`, so every session finds it
whatever folder it starts in. Installing by hand, or from a non-interactive shell, leaves
it unrecorded; set it from a session with

> careerdocs config workspace ~/career-workspace

or

```sh
uv run ~/.codex/plugins/cache/careerdocs-plugin/careerdocs/*/skills/careerdocs/scripts/careerdocs.py config workspace ~/career-workspace
```

Per command, `--workspace <dir>` overrides the recorded default, and a folder that
already holds a `careerdocs.json` is used when a session starts inside it.

## Upload to ChatGPT

ChatGPT takes one skill per zip, with the skill folder at the zip root. Download the
per-skill zips from the
[latest release](https://github.com/bmcnaboe/careerdocs-plugin/releases/latest), then in
ChatGPT open **Skills → Create → Upload from your computer** and upload each one. Skill
uploads are available on workspace plans, where an administrator may need to allow them.
The skills then guide the conversation; generating documents needs an agent that can run
the `careerdocs` CLI, so use Codex for that.

No applicant data ships with the package; you point the skills at your own workspace at
runtime.

## Update and remove

```sh
codex plugin marketplace upgrade careerdocs-plugin
codex plugin add careerdocs@careerdocs-plugin
```

refreshes the marketplace snapshot and reinstalls the current version; re-running the
one-liner does the same. To remove:

```sh
codex plugin remove careerdocs@careerdocs-plugin
codex plugin marketplace remove careerdocs-plugin
```

`install.sh --uninstall` runs both (and removes the Claude Code install) and forgets the
recorded workspace default, leaving the workspace folder itself untouched.
