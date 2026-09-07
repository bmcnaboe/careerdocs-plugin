"""Small shared helpers."""

from __future__ import annotations

from datetime import datetime, timezone


def now() -> str:
    """Current time as an RFC 3339 UTC timestamp (second precision, ``Z`` suffix)."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
