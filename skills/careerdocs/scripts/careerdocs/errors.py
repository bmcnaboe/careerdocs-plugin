"""Typed errors with machine codes and CLI exit codes.

Exit codes follow the CLI contract: 0 ok, 1 a check failed, 2 a contract or usage error.
Every raised error carries a stable ``code`` and a one-sentence message; the CLI prints
``code: message`` to stderr and returns ``exit_code``.
"""

from __future__ import annotations


class CareerDocsError(Exception):
    """Base error. Defaults to a contract/usage failure (exit 2)."""

    code = "ERROR"
    exit_code = 2

    def __init__(self, message: str, *, code: str | None = None, exit_code: int | None = None):
        super().__init__(message)
        if code is not None:
            self.code = code
        if exit_code is not None:
            self.exit_code = exit_code


class UsageError(CareerDocsError):
    code = "USAGE"
    exit_code = 2


class ConfigError(CareerDocsError):
    code = "CONFIG_INVALID"
    exit_code = 2


class WorkspaceError(CareerDocsError):
    """No workspace could be located, or the recorded default is gone."""

    code = "WORKSPACE_UNRESOLVED"
    exit_code = 2


class CheckFailed(CareerDocsError):
    """A verification check failed (exit 1), as opposed to a contract error."""

    code = "CHECK_FAILED"
    exit_code = 1


# --- Provider-contract errors (shared by schema.py and the providers) ---


class ProfileInvalid(CareerDocsError):
    code = "PROFILE_INVALID"
    exit_code = 2


class SchemaTooNew(CareerDocsError):
    code = "SCHEMA_TOO_NEW"
    exit_code = 2


class NotAuthoritative(CareerDocsError):
    code = "NOT_AUTHORITATIVE"
    exit_code = 2


class ApprovalMissing(CareerDocsError):
    code = "APPROVAL_MISSING"
    exit_code = 2


class BaseHashMismatch(CareerDocsError):
    code = "BASE_HASH_MISMATCH"
    exit_code = 2


class ProviderUnreachable(CareerDocsError):
    code = "PROVIDER_UNREACHABLE"
    exit_code = 2
