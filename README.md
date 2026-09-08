# career-documents

A portable, open-source resume and cover-letter plugin for AI coding agents. One
provider-neutral workflow source, packaged thinly for ChatGPT/Codex and Claude
Code/Cowork. It works on its own; agent-layer may install it.

## What it is

`career-documents` turns an applicant's scattered career materials into a single
authoritative profile, then generates tailored resumes and cover letters from it —
mapping a job description to the applicant's real evidence, drafting in their approved
voice and template, and verifying every output before it is called done. Every
deterministic step is a `careerdocs` CLI command; the agent-facing workflow lives in
five Agent Skills that call it.

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

- **Qualifications** — the `CareerProfile`, held by a provider (structured Markdown by
  default, Basic Memory optional as authoritative).
- **Voice** — how the applicant writes, in a `voice.md`.
- **Document templates** — a DOCX template plus a sidecar `template.json` manifest.
- **Target role** — the role brief for one application.

An optional `career-documents.json` only *locates* these; it stores no qualifications
and no credentials.

## No applicant data, ever

Qualifications, voice samples, personal templates, credentials, and generated documents
stay outside this repository. Everything under `examples/` and `templates/` here is
sanitized and fictional. A repository guard fails the build on anything that looks like
real personal data.

## Authoritative updates are proposals

Every change to an applicant's profile is a reviewable diff the applicant approves —
never a silent write. Content is bound to the entities it cites; a factual check rejects
any claim that is not traceable to the profile.

## Install

The repository is the Claude plugin, and the OpenAI package installs the same skills for
Codex/ChatGPT.

**Claude Code / Cowork** — add the marketplace and install the plugin:

```sh
claude plugin marketplace add ./career-documents      # or the GitHub repo URL
claude plugin install career-documents@career-documents
```

**ChatGPT / Codex** — run the standard-library installer:

```sh
python3 packages/openai/install.py                    # links into ~/.agents/skills
```

Full steps and verification: [docs/setup-claude.md](docs/setup-claude.md) and
[docs/setup-codex.md](docs/setup-codex.md).

## Documentation

Start at [docs/README.md](docs/README.md).

## License

MIT — see [LICENSE](LICENSE).
