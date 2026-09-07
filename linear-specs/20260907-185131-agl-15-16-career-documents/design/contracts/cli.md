# CLI Contract: `careerdocs`

Entry point: `skills/career-documents/scripts/careerdocs.py` (run as
`uv run <path>/careerdocs.py ...` or `python3 <path>/careerdocs.py ...`). Every
subcommand accepts `--workspace <dir>` (default: current directory) and `--json` (machine
output on stdout). Human output goes to stdout; diagnostics to stderr. Exit codes: 0 ok,
1 a check failed, 2 contract or usage error.

| Command                                      | Purpose                                                                                   | Reads                             | Writes                                        |
| -------------------------------------------- | ----------------------------------------------------------------------------------------- | --------------------------------- | --------------------------------------------- |
| `doctor`                                     | Report configuration, providers, template, voice, converter, and dependency status       | config, providers                 | nothing                                       |
| `config init`                                | Write a default `career-documents.json` if absent                                          | nothing                           | config                                        |
| `config validate`                            | Validate the config; refuse forbidden keys                                                 | config                            | nothing                                       |
| `profile validate`                           | Validate the authoritative profile against the schema and rules                           | provider                          | nothing                                       |
| `profile import <source>...`                 | Register sources and emit candidate entities (JSON) for the agent to review                | files                             | `sources.jsonl`, `state`                      |
| `profile diff <candidates.json>`             | Merge candidates into a `ProfileDiff` (dedup, precedence, conflicts), render Markdown     | provider, candidates              | `diffs/<diff_id>.json`, `state`               |
| `profile approve <diff_id> [--ops ...]`      | Record the applicant's approval (called only after an explicit yes)                       | diff                              | `approvals.jsonl`                             |
| `profile apply <diff_id>`                    | Apply an approved diff atomically; refresh derived exports; mark stale outputs             | provider, approval                | provider, exports, output records             |
| `profile export --to markdown\|basic_memory` | Produce a derived copy                                                                     | provider                          | target                                        |
| `brief <jd-file-or-url>`                     | Build the role brief skeleton (structured fields the agent completes)                     | JD                                | `applications/<slug>/brief.json`              |
| `map`                                        | Build the requirement-to-evidence map skeleton with candidate evidence per requirement    | brief, profile                    | `applications/<slug>/map.json`                |
| `plan --positioning executive\|builder`      | Build the content plan from the map within the template's page budget; list cuts          | map, profile, template            | `applications/<slug>/plan.json`               |
| `render --kind resume\|cover_letter [--pdf]` | Render the content plan into the template; convert to PDF when a converter exists         | plan, template, voice             | `outputs/<file>.docx`, `.pdf`, `.record.json` |
| `check <document>`                           | Run the five checks; update the output record                                              | document, plan, profile           | `.record.json`, `layout/*.png`                |
| `state show\|answer\|resume <flow> <subject>` | Read or update workflow state                                                            | state                             | state                                         |
| `version`                                    | Print plugin and schema versions                                                           | nothing                           | nothing                                       |

Agent-driven steps (extracting facts from sources, judging direct versus transferable,
drafting prose in voice, deciding positioning) happen between commands: the CLI emits
skeletons and candidates as JSON, the agent fills them, the CLI validates and persists.
