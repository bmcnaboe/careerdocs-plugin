# Output checks

`careerdocs check <document>` runs five checks over a rendered document and writes the
results into its output record (`<document>.record.json`). A document is "done" only when
its record shows every check `pass` or `skipped` with a reason. `check` exits 1 if any
check fails. Each check reports `{ status: pass | fail | skipped, details }`.

## The five checks

1. **Factual traceability** — every content line of the document must be a plan unit (or a
   template-provided string on the template's `allowlist`), and every number and date must
   trace to an entity the plan cites. This is what stops invented qualifications and
   altered metrics. Always runs.

2. **Links / dates** — dates parse, are ordered within a range, and are not in the future;
   links are syntactically valid. Link *liveness* needs the network, so it is recorded as
   skipped offline (the default) rather than failing. Always runs.

3. **Text extraction** — the PDF must carry a real text layer (not an image), and that
   text must be extractable (pypdf). Needs a PDF.

4. **Pagination** — the PDF's page count must fit the template's page budget (pypdf).
   Needs a PDF.

5. **Rendered layout** — content stays inside the margins and within a sane text density
   (pdfplumber), and one PNG per page is rendered for review (pypdfium2). Needs a PDF.

## PDFs and skips

The last three checks need a PDF, produced by `render --pdf` when LibreOffice (`soffice`)
is on PATH. Without it, those three are recorded `skipped` with the reason, and the
document can still be "done" on the strength of the editable-document checks. Fix any
failure at its source — the plan, the draft, or the template — never by weakening a check.

## Output record

Each document records `document`, `kind`, `generated_at`, `plugin_version`,
`schema_version`, the `role_brief` / `map` / `content_plan` paths, `template`, `voice`,
`positioning`, the union of cited `source_ids`, the five `checks`, and `stale` /
`stale_reason` (set when a later profile change invalidates a cited fact). Validated
against `assets/schemas/output-record.schema.json`.
