# Installing careerdocs

The repository is the plugin. Every agent installs it straight from GitHub with its own
plugin manager and keeps its own versioned copy; `bmcnaboe/careerdocs-plugin` is the
short form they all accept.

## Prerequisites

- Claude Code (CLI, desktop app, or IDE extension) or Codex (CLI or app with plugin
  support). Cowork needs nothing installed locally.
- Python 3.10+ or [uv](https://docs.astral.sh/uv/). uv is recommended: the CLI declares
  its dependencies inline and runs under `uv run`; without uv it installs them with pip
  on first run.
- Optional: LibreOffice (`soffice` on PATH) for PDF output and the PDF checks. Without
  it, documents still render as DOCX and those checks report as skipped.
- macOS or Linux. On Windows, use WSL.

## The installer

```bash
curl -fsSL https://raw.githubusercontent.com/bmcnaboe/careerdocs-plugin/main/install.sh | bash
```

It detects Claude Code and Codex, runs the commands below for each, asks which folder
should be your workspace and records it, and prints the Cowork and onboarding steps. It
writes only under `~/.claude`, `~/.codex`, `~/.config/careerdocs`, and the workspace
folder, never asks for sudo, and is safe to re-run. Options go after `bash -s --`:
`--dry-run`, `--uninstall`, `--only claude` or `--only codex`, `--workspace <dir>`.

To read it first:

```bash
curl -fsSLO https://raw.githubusercontent.com/bmcnaboe/careerdocs-plugin/main/install.sh && less install.sh && bash install.sh
```

## By hand

**Claude Code**

```bash
claude plugin marketplace add bmcnaboe/careerdocs-plugin
claude plugin install careerdocs@careerdocs-plugin
```

The install lands at user scope, so it is available in every project. An open session
picks it up after `/reload-plugins`. In the desktop app, once the marketplace is added,
the plugin also appears under the **+** button next to the prompt box, **Plugins**.

**Codex**

```bash
codex plugin marketplace add bmcnaboe/careerdocs-plugin
codex plugin add careerdocs@careerdocs-plugin
```

Restart an open session so it discovers the skills.

**Cowork** keeps its own plugin list, so neither the installer nor the commands above
reach it. In the desktop app open the Cowork tab, then **Customize**, **Plugins**,
**Add marketplace**, enter `bmcnaboe/careerdocs-plugin`, and install **careerdocs**.
Start a new session with your workspace folder attached; that folder is the workspace.
Cowork runs the CLI in its own sandbox; LibreOffice is present in cloud sessions and
absent in local ones.

**claude.ai and ChatGPT** do not run plugins; they take skills as uploads. Download the
per-skill zips from the [latest release](https://github.com/bmcnaboe/careerdocs-plugin/releases/latest)
and add each one (claude.ai: **Customize**, **Skills**; ChatGPT: **Skills**, **Create**,
**Upload from your computer**). The skills then guide the conversation, but generating
documents needs an agent that can run the CLI, so use one of the installs above for that.

**Other agents** in the [Agent Skills](https://agentskills.io) ecosystem get the skills
without the plugin wrapper:

```bash
npx skills add bmcnaboe/careerdocs-plugin -g
```

## The workspace

One folder holds your profile, templates, voice, identity, and generated documents. The
installer records your choice in `~/.config/careerdocs/workspace`, so the skills find it
from any folder. Installed by hand, record it from a session:

> careerdocs config workspace ~/career-workspace

A folder that holds a `careerdocs.json` is used when a session starts inside it, and
`CAREERDOCS_WORKSPACE` or `--workspace <dir>` overrides everything.

## Verify

In any session, say "run careerdocs doctor". It reports the workspace and how it was
found, the configuration, the profile size, templates, voice, identity, LibreOffice, and
dependencies. `claude plugin list` and `codex plugin list` show the installed version.

## Update and remove

Re-running the installer updates every install. By hand:

```bash
claude plugin update careerdocs@careerdocs-plugin
```

```bash
codex plugin marketplace upgrade careerdocs-plugin && codex plugin add careerdocs@careerdocs-plugin
```

Cowork updates from **Update** on the marketplace. To remove everything the installer
set up (the workspace folder is never touched):

```bash
curl -fsSL https://raw.githubusercontent.com/bmcnaboe/careerdocs-plugin/main/install.sh | bash -s -- --uninstall
```
