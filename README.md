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

**Terminal — Claude Code, Codex, or both, detected automatically:**

```sh
curl -fsSL https://raw.githubusercontent.com/bmcnaboe/careerdocs-plugin/main/install.sh | bash
```

Prefer to read it first?

```sh
curl -fsSLO https://raw.githubusercontent.com/bmcnaboe/careerdocs-plugin/main/install.sh && less install.sh && bash install.sh
```

The script needs Python 3.11+ or [uv](https://docs.astral.sh/uv/) (uv recommended),
writes only under `~/.claude` and `~/.agents`, never asks for sudo, and is safe to re-run —
re-running updates. Pass options after `bash -s --`: `--dry-run` previews, `--uninstall`
removes, `--only claude` or `--only codex` limits it to one agent. LibreOffice is optional
and enables PDF output and the PDF checks. macOS and Linux; on Windows use WSL.

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

Manual steps, verification, updates, and removal per platform:
[docs/setup-claude.md](docs/setup-claude.md) and [docs/setup-codex.md](docs/setup-codex.md).

## First run

Open your agent in the folder that holds your résumés, exports, and notes, and say:

> onboard my career documents

The agent inventories what it finds, proposes a workspace configuration, extracts
candidate facts, asks only the questions that matter (conflicts, missing dates, what
should stay private), shows you the resulting profile as a diff, and applies it only after
you say yes. From then on:

> tailor my résumé to this job description: …
> write the matching cover letter
> I just shipped X — add it to my profile
> run careerdocs doctor

Everything it writes stays in your folder; nothing about you is sent anywhere or stored in
this repository.

## The four flows

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
