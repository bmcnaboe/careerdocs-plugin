# Configuration — `careerdocs.json`

The optional `careerdocs.json` at the root of a workspace only *locates* the five
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
| `identity.path` | `identity/identity.md` | The applicant's identity profile: values, personality, motivations, working style, career focus, interests, stories. |
| `outputs.applications_dir` | `applications` | Per-role application folders. |
| `outputs.baselines_dir` | `baselines` | Generated baseline documents. |
| `outputs.file_name` | `{name}-{org}-{role}-{kind}` | Rendered document name. Placeholders: `{name}` (the contact's name), `{org}` (the brief's organization), `{role}` (the brief's role title), `{kind}` (`Resume` / `Cover`), `{slug}`; each is word-slugged and an empty one is dropped. `Jordan-Rivera-Wonka-Industries-Director-of-Engineering-Resume.docx`; a baseline has no organization or role, so `Jordan-Rivera-Resume.docx`. |
| `outputs.history` | `auto` | How a replaced render is kept: `auto` commits to git when the workspace is inside a git work tree with a committer identity and moves it to `outputs/archive/` otherwise; `git` requires the repository; `archive` never uses git. See "Render history". |
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

## Render history

The newest render always carries the plain name, so `outputs/` holds only the current
documents. What happens to the render it replaces depends on `outputs.history`:

- **git** — `render` first commits the previous render when it is not committed yet
  (`chore(<slug>): keep the previous resume render`), then overwrites it in place. Each
  generation or revision round ends with `careerdocs commit --role-slug <slug> -m "<message>"`,
  which stages only that round's paths — the application folder, its workflow state, the
  profile when the round changed it, and any `--path` — and commits them under a
  Conventional Commit message; unrelated changes in the work tree stay untouched.
  `--baseline --positioning <mode>` commits a baseline round, and `--path` alone commits
  setup (the config, templates, voice, identity). Without a repository the command is a
  no-op that says so, so the flows can always run it.
- **archive** — the previous render moves to `outputs/archive/` under its generation
  stamp, with its PDF, record, and layout renders.

`doctor` reports which mode applies and, for git, the repository.

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
  "identity": { "path": "identity/identity.md" },
  "outputs": { "applications_dir": "applications", "baselines_dir": "baselines", "file_name": "{name}-{org}-{role}-{kind}", "history": "auto" },
  "workflow": { "positioning_default": "builder", "page_budget": { "resume": 2, "cover_letter": 1 } }
}
```
