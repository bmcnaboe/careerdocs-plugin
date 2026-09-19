# careerdocs

Tailored résumés and cover letters, written from one trustworthy record of your career,
by the AI coding agent you already use: Claude Code, Codex, or Cowork.

You hand it your existing résumés, a LinkedIn export, and your notes once. It builds one
profile with a source behind every fact. Then, for each job posting, it maps the
requirements to your real experience, agrees an approach with you, drafts in your voice,
fills your template, and checks the result before calling it done. Nothing about you
leaves your machine, and nothing is added to your profile without your yes.

## What you get

- **One profile.** Your roles, achievements, skills, education, projects, and more, each
  traced to the document it came from. Where old résumés disagree, you get a question,
  not a guess.
- **A résumé per posting.** Two pages by default, in your own template, with the evidence
  that matters for that role first. Requirements you do not meet are named as gaps and
  never claimed.
- **A cover letter only you could have written.** Built around why this role fits you,
  in your voice, complementing the résumé instead of repeating it.
- **Checks before "done".** Every line traces to your profile, dates and links are sane,
  and the PDF fits its page target and margins.
- **Your files in one folder**, ready to send.

## Install

You need Claude Code or Codex on macOS or Linux (on Windows, use WSL), plus Python 3.10
or [uv](https://docs.astral.sh/uv/). LibreOffice is optional and enables PDF output.

```bash
curl -fsSL https://raw.githubusercontent.com/bmcnaboe/careerdocs-plugin/main/install.sh | bash
```

The installer finds Claude Code and Codex, installs the plugin into each, and asks which
folder should be your **workspace**: the one place for your profile, templates, voice,
and generated documents (default `~/career-workspace`). Running it again updates.

Cowork, claude.ai, ChatGPT, and other agents: see [docs/install.md](docs/install.md).

## First run: onboard

Open a new session and run the onboard skill.

| Agent | Run |
| --- | --- |
| Claude Code | `/careerdocs:onboard` |
| Codex | `$onboard` |
| Cowork | `/careerdocs:onboard`, with your workspace folder attached to the session |

It asks for your materials one at a time (résumés old and new, the LinkedIn data export,
notes, writing samples), explains how to get each, imports them, asks only the questions
your documents raise, and shows you the proposed profile before writing anything. Then it
sets up your résumé and letter templates, captures how you write, and asks a few questions
about who you are beyond the facts, so your letters have a through-line of your own. It
ends with a short tour.

Run it again any time. It only does what is missing.

## Applying to a job: apply

Paste a posting into a new session and run the apply skill: `/careerdocs:apply` or
`$apply`. Say whether you want the résumé, the letter, or both. In one short conversation
it:

1. Reads the posting and confirms the organization, the role, and what you want.
2. Shows the fit: which requirements you meet directly, which transfer, which are gaps,
   and which of the posting's keywords your profile lacks. It asks which of those you
   genuinely have and records only those, with your approval.
3. Proposes an approach and confirms it in one exchange: positioning (leadership first or
   hands-on first), the three pieces of evidence that lead, what to compress, résumé
   length, letter length and tone, and anything to avoid.
4. For the letter, asks why this role, in your words.
5. Drafts, renders, and checks each document, then reports what was cut for space and
   which requirements remain gaps.

Interrupted? Run it again for the same posting; it continues where it stopped.

## Keeping your profile current: update

A new job, a certification, a shipped project, or a wrong date: run the update skill,
`/careerdocs:update` or `$update`, and say what changed. It records your statement as the
source, shows you the change, applies it after your yes, and tells you which earlier
documents are now out of date.

## Your workspace

| Folder or file | What it holds |
| --- | --- |
| `profile/` | your profile, one file per fact, with the record of every source, approval, and change |
| `sources/` | the documents you imported |
| `templates/` | your résumé and letter templates |
| `voice/voice.md`, `identity/identity.md` | how you write; who you are beyond the facts |
| `applications/<role>/` | the posting, the brief and map, and the finished documents |
| `baselines/` | untargeted résumés |

Documents are named `<Your Name>-<Organization>-<Role>-Resume.docx` and `-Cover.docx`,
with PDFs when LibreOffice is installed. If your workspace is a git repository (onboard
offers to make it one), every round is committed there; otherwise a replaced version
moves to an `archive/` folder beside the new one.

## Privacy

Everything stays in your workspace. The plugin itself sends nothing anywhere (its first
run may download its Python libraries); the agent you run talks to its model as it always
does. This repository holds no applicant data; its examples are fictional.

## Documentation

- [docs/install.md](docs/install.md): every platform, verifying, updating, removing.
- [docs/templates-and-voice.md](docs/templates-and-voice.md): restyling your templates,
  the voice profile, and the identity profile.
- [DEVELOPMENT.md](DEVELOPMENT.md): how the plugin is built, tested, and released.

MIT license, see [LICENSE](LICENSE).
