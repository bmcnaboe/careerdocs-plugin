# Configuration reference

`careerdocs.json` at the workspace root locates the four authorities and workflow
policy; it stores no qualifications and no credentials. Every key has a default, so the
file is optional. `careerdocs config init` writes a default; `careerdocs config validate`
checks it and refuses forbidden content. Validated against `assets/schemas/config.schema.json`.

| Key | Default | Meaning |
| --- | --- | --- |
| `version` | `"1"` | config schema version |
| `providers.authoritative` | `markdown` | `markdown` or `basic_memory` |
| `providers.markdown.path` | `profile` | structured-Markdown directory (and the derived export when Basic Memory is authoritative) |
| `providers.basic_memory.vault_path` | — | vault path (required when Basic Memory is authoritative) |
| `providers.basic_memory.project` | — | Basic Memory project |
| `providers.basic_memory.folder` | `career` | folder within the vault |
| `templates.dir` | `templates` | template folders live here |
| `templates.resume` | `resume` | résumé template subfolder |
| `templates.cover_letter` | `cover-letter` | cover-letter template subfolder |
| `voice.path` | `voice/voice.md` | voice profile |
| `outputs.applications_dir` | `applications` | per-role folders |
| `outputs.baselines_dir` | `baselines` | generated baselines |
| `workflow.state_dir` | `.careerdocs/state` | resumable state |
| `workflow.positioning_default` | `builder` | `executive` or `builder` |
| `workflow.page_budget.resume` | `2` | résumé pages |
| `workflow.page_budget.cover_letter` | `1` | letter pages |
| `workflow.approval_mode` | `explicit` | only `explicit` in this version |

**Forbidden anywhere in the file**: credential-like keys/values (`password`, `token`,
`api_key`, `secret`) and qualification content (`entities`, `experience`, `skills`,
`achievements`). Those belong in the profile provider.

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
