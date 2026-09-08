# Configuration reference

`career-documents.json` at the workspace root locates the four authorities and workflow
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
| `workflow.state_dir` | `.career-documents/state` | resumable state |
| `workflow.positioning_default` | `builder` | `executive` or `builder` |
| `workflow.page_budget.resume` | `2` | résumé pages |
| `workflow.page_budget.cover_letter` | `1` | letter pages |
| `workflow.approval_mode` | `explicit` | only `explicit` in this version |

**Forbidden anywhere in the file**: credential-like keys/values (`password`, `token`,
`api_key`, `secret`) and qualification content (`entities`, `experience`, `skills`,
`achievements`). Those belong in the profile provider.
