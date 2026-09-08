# Setup — ChatGPT / Codex

The OpenAI package is a manifest plus a standard-library installer that places the same
`skills/` into the location Codex discovers skills from, and prints the manual steps for
uploading them to ChatGPT.

## Prerequisites

- Codex CLI, or ChatGPT with skill upload.
- Python 3.11+ on PATH. [uv](https://docs.astral.sh/uv/) is recommended for the
  `careerdocs` CLI; `python3` with the dependencies installed also works.
- Optional: LibreOffice (`soffice` on PATH) for PDF conversion.

## Install for Codex

From a local clone, run the installer. It links each skill into `~/.agents/skills/` by
default (use `--copy` for a standalone copy):

```sh
python3 packages/openai/install.py            # symlink into ~/.agents/skills
python3 packages/openai/install.py --copy     # copy instead of link
python3 packages/openai/install.py --dry-run  # preview without changing anything
python3 packages/openai/install.py --home /some/other/home
python3 packages/openai/install.py --uninstall
```

The installer refuses to run if the manifest disagrees with the `skills/` tree, so an
install always matches the source.

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

The installer prints these steps after a successful install:

1. In ChatGPT, open Settings → Skills (or the skill upload dialog).
2. For each skill under `skills/<name>/`, upload its `SKILL.md` and referenced files.
3. Keep the skill name identical to the directory name so invocations match Codex.

No applicant data ships with the package; you point the skills at your own workspace at
runtime.
