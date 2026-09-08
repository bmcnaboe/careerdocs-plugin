# Setup — Codex and ChatGPT

Codex reads Agent Skills from `~/.agents/skills` (user scope) and from `.agents/skills`
inside a repository. The OpenAI package here is a manifest plus a standard-library
installer that places the plugin's five skills in the user-scope location; ChatGPT takes
the same skills as zip uploads.

## Prerequisites

- Codex CLI, or ChatGPT on a plan that allows skill uploads.
- Python 3.11+ or [uv](https://docs.astral.sh/uv/) (uv recommended for the `careerdocs`
  CLI; `python3` with the dependencies installed also works).
- Optional: LibreOffice (`soffice` on PATH) for PDF conversion.

## Install for Codex

The one-liner detects Codex, downloads the repository archive, and runs the installer
below in copy mode (and installs for Claude Code too when it finds it):

```sh
curl -fsSL https://raw.githubusercontent.com/bmcnaboe/careerdocs-plugin/main/install.sh | bash
```

From a local clone, run the installer directly. It links each skill into
`~/.agents/skills/` by default (use `--copy` for a standalone copy):

```sh
python3 packages/openai/install.py            # symlink into ~/.agents/skills
python3 packages/openai/install.py --copy     # copy instead of link
python3 packages/openai/install.py --dry-run  # preview without changing anything
python3 packages/openai/install.py --home /some/other/home
python3 packages/openai/install.py --uninstall
```

The installer refuses to run if the manifest disagrees with the `skills/` tree, so an
install always matches the source. Codex's built-in `$skill-installer` can also fetch a
single skill from its GitHub folder, for example
`https://github.com/bmcnaboe/careerdocs-plugin/tree/main/skills/careerdocs`, one skill at
a time. Restart Codex after installing so it discovers the new skills.

## Verify

```sh
ls ~/.agents/skills
```

lists the installed skills. Each installed `SKILL.md` is byte-identical to its source.
Confirm the CLI:

```sh
uv run ~/.agents/skills/careerdocs/scripts/careerdocs.py version
```

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

Re-running the one-liner updates the copied skills. `install.sh --uninstall` removes them
(and the Claude Code plugin, when present); from a clone, `python3
packages/openai/install.py --uninstall` does the same for Codex alone.
