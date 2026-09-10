# Configuration — `careerdocs.json`

The optional `careerdocs.json` at the root of a workspace only *locates* the four
authorities and workflow policy. It stores no qualifications and no credentials. Every key
has a default, so the file is optional; `careerdocs config init` writes a default one, and
`careerdocs config validate` checks it and refuses forbidden content.

Validated against `assets/schemas/config.schema.json`.

## Keys

| Key | Default | Meaning |
| --- | --- | --- |
| `version` | `"1"` | Config schema version. |
| `providers.authoritative` | `markdown` | Which provider holds the authoritative profile: `markdown` or `basic_memory`. |
| `providers.markdown.path` | `profile` | Directory for the structured-Markdown profile (and the derived export when Basic Memory is authoritative). |
| `providers.basic_memory.vault_path` | — | Path to the Basic Memory vault (required when Basic Memory is authoritative). |
| `providers.basic_memory.project` | — | The Basic Memory project name. |
| `providers.basic_memory.folder` | `career` | Folder within the vault for the profile notes. |
| `templates.dir` | `templates` | Directory holding template subfolders. |
| `templates.resume` | `resume` | Résumé template subfolder (contains `template.docx` + `template.json`). |
| `templates.cover_letter` | `cover-letter` | Cover-letter template subfolder. |
| `voice.path` | `voice/voice.md` | The applicant's voice profile. |
| `outputs.applications_dir` | `applications` | Per-role application folders. |
| `outputs.baselines_dir` | `baselines` | Generated baseline documents. |
| `outputs.file_name` | `{name}-{kind}` | Rendered document name; placeholders `{name}` (the contact's name), `{kind}` (`Resume` / `Cover-Letter`), `{org}` (the brief's organization), `{slug}`. The newest render carries this name; a replaced render moves to `archive/` under its generation stamp. |
| `workflow.state_dir` | `.careerdocs/state` | Resumable workflow state. |
| `workflow.positioning_default` | `builder` | Default positioning (`executive` or `builder`). |
| `workflow.page_budget.resume` | `2` | Résumé page budget. |
| `workflow.page_budget.cover_letter` | `1` | Cover-letter page budget. |
| `workflow.approval_mode` | `explicit` | Only `explicit` in this version — every write is an approved diff. |

## Locating the workspace

Every command runs against one workspace directory, resolved once per invocation; the
first of these that applies wins:

1. `--workspace <dir>` on the command line;
2. the `CAREERDOCS_WORKSPACE` environment variable;
3. the nearest directory at or above the current one that holds `careerdocs.json`;
4. the recorded default — one absolute path in `~/.config/careerdocs/workspace`
   (`$XDG_CONFIG_HOME/careerdocs/workspace`), written by the installer or by
   `careerdocs config workspace <dir>`;
5. the current directory.

Only the last is *unestablished*: nothing marks that directory as a workspace, so
commands that read or write applicant data there fail with `WORKSPACE_UNRESOLVED`
instead of scattering files into an arbitrary folder. `version`, `doctor`, `config init`,
`config workspace`, `inventory`, and `organize` still run. `careerdocs config workspace`
with no argument shows what resolved and how; with `<dir>` it creates the directory if
needed, records it as the default, and writes its `careerdocs.json`. A recorded default
that no longer exists is an error, not a silent fallback. `doctor` also names the source.

## Forbidden content

`config validate` refuses the file if any key or string value looks like a credential
(`password`, `token`, `api_key`, `secret`) or qualification content (`entities`,
`experience`, `skills`, `achievements`). Those belong in the profile provider, never in
the config.

## Example

```json
{
  "version": "1",
  "providers": { "authoritative": "markdown", "markdown": { "path": "profile" } },
  "templates": { "dir": "templates", "resume": "resume", "cover_letter": "cover-letter" },
  "voice": { "path": "voice/voice.md" },
  "outputs": { "applications_dir": "applications", "baselines_dir": "baselines", "file_name": "{name}-{kind}" },
  "workflow": { "positioning_default": "builder", "page_budget": { "resume": 2, "cover_letter": 1 } }
}
```
