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
| US2-1    | integration         | `tests/integration/test_onboard.py::test_conflict_one_question` | pending |
| US2-2    | integration         | `tests/integration/test_onboard.py::test_apply_single_entry` | pending |
| US2-3    | integration         | `tests/integration/test_onboard.py::test_resume_no_repeat` | pending |
| US2-4    | integration         | `tests/integration/test_onboard.py::test_private_excluded` | pending |
| US2-5    | integration         | `tests/integration/test_basic_memory_provider.py`     | pending |
| US3-1    | integration         | `tests/integration/test_resume.py::test_pipeline_artifacts` | pending |
| US3-2    | integration         | `tests/integration/test_resume.py::test_gap_never_claimed` | pending |
| US3-3    | unit + integration  | `tests/unit/test_plan.py::test_positioning_inverts`; `test_resume.py` | pending |
| US3-4    | integration         | `tests/integration/test_resume.py::test_five_checks`  | pending |
| US3-5    | unit                | `tests/unit/test_plan.py::test_budget_cuts_reported`  | pending |
| US4-1    | integration         | `tests/integration/test_cover_letter.py::test_reuses_brief_and_map` | pending |
| US4-2    | integration         | `tests/integration/test_cover_letter.py::test_checks_and_budget` | pending |
| US4-3    | integration         | `tests/integration/test_cover_letter.py::test_no_verbatim_bullets` | pending |
| US5-1    | integration         | `tests/integration/test_update.py::test_new_fact_provenance` | pending |
| US5-2    | integration         | `tests/integration/test_update.py::test_exports_agree_and_stale` | pending |
| US5-3    | integration         | `tests/integration/test_update.py::test_resume_pending_diff` | pending |
