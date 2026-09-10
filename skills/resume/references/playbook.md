# Résumé playbook

Generate a tailored résumé. `<dir>` below is the resolved workspace (`doctor` shows it;
`--workspace <dir>` only overrides it); artifacts land in `applications/<role-slug>/`.

## 1. Brief

```sh
careerdocs brief applications/<slug>/job-description.md --workspace <dir> --json
```

Fill in the organization, role, and seniority on the generated `brief.json`, refine the
requirement text if needed, and keep each requirement's stable id. Validate:

```sh
careerdocs brief applications/<slug>/brief.json --validate --workspace <dir>
```

## 2. Map

```sh
careerdocs map --role-slug <slug> --workspace <dir> --json
```

The CLI proposes evidence and a classification per requirement. Confirm each with real
judgement and edit `map.json`:

- **direct** — the profile clearly satisfies it (a matching skill or achievement).
- **transferable** — adjacent experience that partly applies; say why in `why`/`note`.
- **gap** — no honest support. Leave `evidence` empty. Do not stretch a fact to cover it.

Validate: `careerdocs map --validate applications/<slug>/map.json`.

## 2b. Keyword coverage

```sh
careerdocs brief applications/<slug>/brief.json --coverage --workspace <dir> --json
```

Lists each requirement keyword the visible profile does not contain literally. Automated
screeners match words, so judge each miss: a synonym of existing evidence is reworded with
the posting's term when drafting (the fact does not change); a skill the applicant
genuinely has but the profile lacks goes through the update flow — statement provenance,
their explicit yes — and then `map` again; anything else stays absent. Never add a keyword
the applicant has not confirmed.

## 3. Choose positioning

Pick **executive** (leadership, scope, outcomes first) or **builder** (hands-on delivery
first). The recommendation is in the brief; the applicant decides. Positioning changes
what is emphasized and in what order — never the facts.

## 4. Plan

```sh
careerdocs plan --positioning <executive|builder> --kind resume --role-slug <slug> --workspace <dir> --json
```

Selects and orders evidence within the template's page budget and lists cuts. Review the
cut list; if something important was cut, adjust emphasis (positioning) or the template
budget rather than inflating claims.

## 5. Draft in voice

Rewrite each unit's `text` in the applicant's voice (`voice.md`): verb-first, concrete,
no banned phrases. Every claim must still trace to the unit's `source_ids`. Do not add a
fact that is not in the profile. Keep a role line as `Title, Organization<tab>dates`, with
any descriptor on the role's summary line (`role_summaries` in the manifest), never inside
the role line: parsers read the whole line as the title and company.

## 6. Render

```sh
careerdocs render --kind resume --pdf --role-slug <slug> --workspace <dir>
```

Writes `<Name>-Resume.docx` (and `.pdf` when LibreOffice is present) and an output record
skeleton. A previous render of that name is rotated to a `_bak1` suffix (`_bak1` to
`_bak2`, and so on) with its PDF, record, and layout renders, so nothing is lost and the
newest document always carries the plain name.

## 7. Check

```sh
careerdocs check applications/<slug>/outputs/<Name>-Resume.docx --workspace <dir>
```

Runs factual, links/dates, extraction, pagination, and layout. Fix any failure at its
source (the plan, the draft, the template) — never by weakening a check. The document is
done only when the record shows every check passed or skipped with a reason.

## 8. Report cuts and gaps

Tell the applicant what was cut for space and which requirements are gaps, and let them
decide whether to proceed, re-emphasize, or acquire the missing qualification.
