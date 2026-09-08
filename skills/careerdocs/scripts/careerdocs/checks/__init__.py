"""Output checks.

Each check takes the rendered document (and, where needed, the plan and profile) and
returns ``{"status": "pass"|"fail"|"skipped", "details": str}``. A document is only "done"
when its output record shows every check passed or was skipped with a reason.
"""
