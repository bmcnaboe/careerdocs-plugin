# careerdocs-plugin

Tailored résumés and cover letters from one authoritative profile, for AI coding agents.
One provider-neutral workflow source, packaged for Claude Code and ChatGPT/Codex.

## What it is

`careerdocs-plugin` turns an applicant's scattered career materials into a single
authoritative profile, then generates tailored résumés and cover letters from it —
mapping a job description to the applicant's real evidence, drafting in their approved
voice and template, and verifying every output before it is called done. Every
deterministic step is a `careerdocs` CLI command; the agent-facing workflow lives in five
Agent Skills that call it.

## Install

Every environment installs the plugin straight from this repository with its own plugin
manager and keeps its own versioned copy; nothing is copied by hand, and every update
comes from the same source. `bmcnaboe/careerdocs-plugin` is the short GitHub form all of
them accept.

### One command: Claude Code and Codex

```sh
curl -fsSL https://raw.githubusercontent.com/bmcnaboe/careerdocs-plugin/main/install.sh | bash
```

Prefer to read it first?

```sh
curl -fsSLO https://raw.githubusercontent.com/bmcnaboe/careerdocs-plugin/main/install.sh && less install.sh && bash install.sh
```

The script detects Claude Code and Codex and runs the commands below for each, asks which
folder should be your workspace and records it, and ends with the Cowork and onboarding
steps. It needs Python 3.10+ or [uv](https://docs.astral.sh/uv/) (uv recommended), writes
only under `~/.claude`, `~/.codex`, `~/.config/careerdocs`, and the workspace folder,
never asks for sudo, and is safe to re-run — re-running updates. Pass options after
`bash -s --`: `--dry-run` previews, `--uninstall` removes, `--only claude` or
`--only codex` limits it to one agent, `--workspace <dir>` answers the workspace prompt up
front. LibreOffice is optional and enables PDF output and the PDF checks. macOS and Linux;
on Windows use WSL.

### By environment

**Claude Code** (CLI, desktop app, IDE extensions):

```sh
claude plugin marketplace add bmcnaboe/careerdocs-plugin
claude plugin install careerdocs@careerdocs-plugin
```

Update with `claude plugin update careerdocs@careerdocs-plugin`.

**Codex** (CLI or app, with plugin support):

```sh
codex plugin marketplace add bmcnaboe/careerdocs-plugin
codex plugin add careerdocs@careerdocs-plugin
```

Update with `codex plugin marketplace upgrade careerdocs-plugin` followed by the same
`codex plugin add`.

**Cowork** (Claude desktop app): nothing to install on your machine. In the Cowork tab
open **Customize → Plugins**, select **Add marketplace**, enter
`bmcnaboe/careerdocs-plugin`, and install **careerdocs**. **Update** on the marketplace
pulls new versions. Cowork keeps its own plugin list, so the commands above do not reach
it.

**No terminal — ChatGPT or claude.ai:** download the per-skill zips from the
[latest release](https://github.com/bmcnaboe/careerdocs-plugin/releases/latest) and upload
each one (ChatGPT: Skills → Create → Upload from your computer; claude.ai: Customize →
Skills → Add). The skills then guide the conversation, but generating documents needs an
agent that can run the `careerdocs` CLI, so use a terminal install for that.

**Other agents** — Cursor, GitHub Copilot, Gemini CLI, OpenCode, and the rest of the
[Agent Skills](https://agentskills.io) ecosystem — get the skills without the plugin
wrapper:

```sh
npx skills add bmcnaboe/careerdocs-plugin -g
```

Verification, updates, and removal per platform:
[docs/setup-claude.md](docs/setup-claude.md) and [docs/setup-codex.md](docs/setup-codex.md).

## First run

The installer asks for a **workspace**: the one folder that holds your profile, templates,
voice, and generated documents (default `~/career-workspace`). It records the choice in
`~/.config/careerdocs/workspace`, so the skills find it from any folder. Per command,
`--workspace <dir>` overrides it; `careerdocs config workspace <dir>` changes the default.
In Cowork, the folder you attach to the session is the workspace.

Then open a new agent session and run the onboard skill. It checks what is already set
up, walks you through gathering your materials (résumés, the LinkedIn data export, notes,
writing samples), builds your profile as a diff you approve, sets up templates and voice,
and ends with a short tour:

| Agent | Run |
| --- | --- |
| Claude Code | `/careerdocs:onboard` |
| Cowork | `/careerdocs:onboard` in a session with the workspace folder attached; if `/` does not offer it, say "onboard my career documents" |
| Codex | `$onboard` |

From then on, per application:

| | Claude Code and Cowork | Codex |
| --- | --- | --- |
| Tailor a résumé to a job description | `/careerdocs:resume` | `$resume` |
| Write the matching cover letter | `/careerdocs:cover-letter` | `$cover-letter` |
| Add a new achievement or correction to your profile | `/careerdocs:update` | `$update` |
| The whole application for one posting, guided | `/careerdocs:apply` | `$apply` |

Plain requests work too ("tailor my résumé to this job description: …"); the skill
command is the reliable way to start a flow. "Run careerdocs doctor" shows what is
configured, including which workspace resolved and how.

Everything it writes stays in your workspace; nothing about you is sent anywhere or stored
in this repository.

## The five flows

1. **Onboard / import** — inventory existing sources (resumes, exports, notes), extract
   candidate facts, reconcile them into one profile, and ask only the questions that
   matter.
2. **Update qualifications** — capture a new fact with provenance, propose it as a
   reviewable diff, and report which past outputs it makes stale.
3. **Tailored resume** — turn a job description into a role brief, map each requirement
   to direct / transferable / gap evidence, plan the content, render it, and run the
   checks.
4. **Complementary cover letter** — reuse the brief and map to draft a letter that
   complements the resume rather than repeating it.
5. **Apply** — a short guided interview that runs the three flows above for one posting:
   fit and gaps, qualifications you confirm, an agreed approach (positioning, emphasis,
   length, tone), then both documents checked and reported.

## The four authorities

Kept separate, never folded into one opaque profile:

- **Qualifications** — the `CareerProfile`, held by a provider — structured Markdown under
  `profile/` in the workspace by default; a Basic Memory provider also exists.
- **Voice** — how the applicant writes, in a `voice.md`.
- **Document templates** — a DOCX template plus a sidecar `template.json` manifest.
- **Target role** — the role brief for one application.

An optional `careerdocs.json` only *locates* these; it stores no qualifications and no
credentials.

## No applicant data, ever

Qualifications, voice samples, personal templates, credentials, and generated documents
stay outside this repository. Everything under `examples/` and `templates/` here is
sanitized and fictional. A repository guard fails the build on anything that looks like
real personal data.

## Authoritative updates are proposals

Every change to an applicant's profile is a reviewable diff the applicant approves —
never a silent write. Content is bound to the entities it cites; a factual check rejects
any claim that is not traceable to the profile.

## Documentation

Start at [docs/README.md](docs/README.md). Guides:

- Setup: [docs/setup-claude.md](docs/setup-claude.md), [docs/setup-codex.md](docs/setup-codex.md)
- [docs/configuration.md](docs/configuration.md) — the optional `careerdocs.json`
- [docs/profile-schema.md](docs/profile-schema.md) — the versioned `CareerProfile` model
- [docs/provider-contract.md](docs/provider-contract.md) — the provider interface and the two providers
- [docs/checks.md](docs/checks.md) — the five output checks
- [docs/templates-and-voice.md](docs/templates-and-voice.md) — authoring templates and the voice profile
- [docs/migration.md](docs/migration.md) — migrating an existing career folder

## License

MIT — see [LICENSE](LICENSE).
