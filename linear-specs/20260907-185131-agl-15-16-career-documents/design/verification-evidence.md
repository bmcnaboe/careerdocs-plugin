# Verification Evidence: Portable Resume and Cover-Letter Plugin

Outcome map for every acceptance scenario in [spec.md](spec.md). The run plan's evidence tasks
update these rows before each story's verification task; `scripts/verification_evidence_check.py`
fails when a scenario has no row or a row has no evidence.

Status values: `pending`, `pass`, `fail`, `skipped (reason)`.

| Scenario | Method              | Evidence                                              | Status  |
| -------- | ------------------- | ----------------------------------------------------- | ------- |
| US1-1    | manual-acceptance   | quickstart §Manual acceptance item 1 (Claude); `docs/setup-claude.md` | skipped (manual acceptance) |
| US1-2    | manual-acceptance   | quickstart §Manual acceptance item 1 (Codex); `docs/setup-codex.md`   | skipped (manual acceptance) |
| US1-3    | contract            | `scripts/check_inventory.py` (full gate: consistent); `tests/integration/test_packages.py::test_inventory_has_zero_differences` | pass    |
| US1-4    | contract            | `scripts/pii_guard.py` (final gate: zero findings across the tracked tree) | pass    |
| US2-1    | integration         | `tests/integration/test_onboard.py::test_conflict_one_question`; unit: `test_merge.py`, `test_questions.py::test_example_yields_exactly_one_question` | pass    |
| US2-2    | integration         | `tests/integration/test_onboard.py::test_apply_single_entry`; unit: `test_diff.py`, `test_merge.py::test_merged_diff_applies_cleanly` | pass    |
| US2-3    | integration         | `tests/integration/test_onboard.py::test_resume_no_repeat`; unit: `test_state.py`, `test_questions.py::test_no_question_repeats_after_resume` | pass    |
| US2-4    | integration         | `tests/integration/test_onboard.py::test_private_excluded`; unit: `test_visibility.py::test_export_excludes_private_and_is_derived` | pass    |
| US2-5    | integration         | `tests/integration/test_basic_memory_provider.py`; unit: `test_basic_memory_provider.py` (same ids, derived markdown export) | pass    |
| US3-1    | integration         | `tests/integration/test_resume.py::test_pipeline_artifacts`; unit: `test_brief.py`, `test_mapping.py`, `test_plan.py`, `test_render.py` | pass    |
| US3-2    | integration         | `tests/integration/test_resume.py::test_gap_never_claimed`; unit: `test_mapping.py::test_fda_requirement_is_a_gap`, `test_checks_factual.py` | pass    |
| US3-3    | unit + integration  | `tests/unit/test_plan.py::test_positioning_inverts`; `tests/integration/test_resume.py::test_positioning_inverts` | pass    |
| US3-4    | integration         | `tests/integration/test_resume.py::test_five_checks`; unit: `test_record.py`, `test_checks_layout.py` | pass    |
| US3-5    | unit                | `tests/unit/test_plan.py::test_budget_cuts_reported` | pass    |
| US4-1    | integration         | `tests/integration/test_cover_letter.py::test_reuses_brief_and_map`; unit: `test_plan.py::test_cover_letter_orders_by_requirement_value` | pending |
| US4-2    | integration         | `tests/integration/test_cover_letter.py::test_checks_and_budget`; unit: `test_plan.py::test_cover_letter_page_budget_cuts`, `test_checks_factual.py` | pending |
| US4-3    | integration         | `tests/integration/test_cover_letter.py::test_no_verbatim_bullets`; unit: `test_checks_factual.py::test_verbatim_bullet_check_flags_reuse` | pending |
| US5-1    | integration         | `tests/integration/test_update.py::test_new_fact_provenance` | pending |
| US5-2    | integration         | `tests/integration/test_update.py::test_exports_agree_and_stale` | pending |
| US5-3    | integration         | `tests/integration/test_update.py::test_resume_pending_diff` | pending |
