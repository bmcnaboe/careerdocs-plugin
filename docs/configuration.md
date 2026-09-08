# Configuration — `career-documents.json`

The optional `career-documents.json` at the root of a workspace only *locates* the four
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
| `workflow.state_dir` | `.career-documents/state` | Resumable workflow state. |
| `workflow.positioning_default` | `builder` | Default positioning (`executive` or `builder`). |
| `workflow.page_budget.resume` | `2` | Résumé page budget. |
| `workflow.page_budget.cover_letter` | `1` | Cover-letter page budget. |
| `workflow.approval_mode` | `explicit` | Only `explicit` in this version — every write is an approved diff. |

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
  "outputs": { "applications_dir": "applications", "baselines_dir": "baselines" },
  "workflow": { "positioning_default": "builder", "page_budget": { "resume": 2, "cover_letter": 1 } }
}
```
