# Checks reference

`careerdocs check <document>` runs five checks and writes the results into the document's
output record. A document is "done" only when the record shows every check `pass` or
`skipped` with a reason. `check` exits 1 on any failure. Each check reports
`{ status: pass | fail | skipped, details }`.

1. **Factual traceability** (always) — every content line is a plan unit, one line of a
   multi-line unit (the contact unit's name and details lines), a template allowlist
   string, or a line the render composed from the brief and the calendar (the letter's
   role line and date, the record's `template_lines`), compared with whitespace
   collapsed; every number and date traces to a cited entity or a composed line. Stops
   invented qualifications and altered metrics.
2. **Links / dates** (always) — dates parse, are ordered, and are not in the future; links
   are well-formed. Link liveness is skipped offline.
3. **Text extraction** (needs a PDF) — the PDF carries an extractable text layer.
4. **Pagination** (needs a PDF) — a résumé matches its target of two pages by default
   (one only on express request); other documents fit their page budget.
5. **Rendered layout** (needs a PDF) — content within margins and a sane density, the
   contact line on one line; a PNG per page is rendered.

The three PDF checks need `render --pdf`, which needs LibreOffice (`soffice`). Without it
they are `skipped` with the reason. Fix a failure at its source — the plan, the draft, or
the template — never by weakening a check.

The output record (validated against `assets/schemas/output-record.schema.json`) stores the
document, kind, timestamps, versions, the brief/map/plan paths, template, voice,
positioning, the union of cited `source_ids`, the `template_lines`, the five checks, and `stale` / `stale_reason`
(set when a later profile change invalidates a cited fact).
