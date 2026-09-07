# Artifact Contracts

Shapes referenced by the CLI contract, validated by the schemas under
`skills/career-documents/assets/schemas/`
(`role-brief.schema.json`, `requirement-map.schema.json`, `content-plan.schema.json`,
`output-record.schema.json`, `workflow-state.schema.json`). Field definitions are in
`data-model.md`; this file fixes file names, locations, and invariants.

| Artifact          | Location                                                    | Invariants                                                                                          |
| ----------------- | ----------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| Role brief        | `<applications_dir>/<role-slug>/brief.json`                 | Every requirement has a stable `id`; `recommended_positioning` is one of the two modes              |
| Requirement map   | `<applications_dir>/<role-slug>/map.json`                   | Every `requirement_id` in the brief appears exactly once; `gap` entries have empty `evidence`       |
| Content plan      | `<applications_dir>/<role-slug>/plan.json`                  | Every unit has ≥1 `source_ids` unless its `section_id` is on the template allowlist; no `gap` requirement is cited as satisfied |
| Rendered document | `<applications_dir>/<role-slug>/outputs/<kind>-<stamp>.docx` (+ `.pdf`) | File name carries kind and timestamp; never overwrites                                   |
| Output record     | next to the document, `<name>.record.json`                  | `source_ids` equals the union of the plan's unit sources; every check has a status                  |
| Layout renders    | `<applications_dir>/<role-slug>/outputs/layout/<name>-p<N>.png` | One image per page                                                                              |
| Workflow state    | `<state_dir>/<flow>/<subject>.json`                         | Append-only `questions[]`; a question id is never asked twice                                       |
| Baselines         | `<baselines_dir>/<positioning>/<kind>-<stamp>.docx` (+ record) | Same record shape; `role_brief` is null                                                          |
