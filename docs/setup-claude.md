# Setup — Claude Code / Cowork

The repository *is* the plugin: its `.claude-plugin/` manifests and `skills/` tree are
consumed in place, so installing is adding the marketplace and installing the plugin.

## Prerequisites

- Claude Code (CLI, desktop, or IDE extension) or Cowork.
- Python 3.11+ on PATH. [uv](https://docs.astral.sh/uv/) is recommended — the
  `careerdocs` CLI declares its dependencies inline and runs under `uv run`.
- Optional: LibreOffice (`soffice` on PATH) for PDF conversion. Without it, editable
  documents still render and the pagination/layout checks report as skipped.

## Install

Add the marketplace, then install the plugin. From a local clone:

```sh
claude plugin marketplace add ./career-documents      # or the GitHub repo URL
claude plugin install career-documents@career-documents
```

The two arguments are `<plugin>@<marketplace>`; both are named `career-documents`.

## Cowork

Cowork uses the same plugin format. Add the marketplace and install the plugin from
Cowork's plugin settings; the skills and the `careerdocs` CLI come across unchanged. No
applicant data ships with the plugin — you point it at your own workspace at runtime.

## Verify

```sh
claude plugin details career-documents
```

lists the installed skills — the core `career-documents` skill plus the flow skills
(`career-onboard`, `career-update`, `career-resume`, `career-cover-letter`). To confirm
the CLI itself:

```sh
uv run <plugin-root>/skills/career-documents/scripts/careerdocs.py version
uv run <plugin-root>/skills/career-documents/scripts/careerdocs.py doctor --workspace <your-workspace>
```

`doctor` reports your configuration, providers, template, voice, converter, and
dependency status.
