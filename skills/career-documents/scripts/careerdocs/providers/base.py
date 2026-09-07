"""Provider interface, canonical hashing, and the typed provider-contract errors.

A provider stores the authoritative ``CareerProfile`` or a derived copy. This module
defines the abstract interface every provider implements — reading and writing the
profile, a content hash stable across file order, the source/approval/diff ledgers, an
export to another provider, and a capabilities report — plus the shared canonical hash so
every provider hashes identical content identically.

The diff → approve → apply orchestration (the contract's ``propose``/``apply``) lives in
``careerdocs.diff`` over these primitives; providers own storage, not the approval logic.
"""

from __future__ import annotations

import hashlib
import json
from abc import ABC, abstractmethod

# Re-exported so provider code can raise the contract's typed errors from one place.
from ..errors import (  # noqa: F401
    ApprovalMissing,
    BaseHashMismatch,
    NotAuthoritative,
    ProfileInvalid,
    ProviderUnreachable,
    SchemaTooNew,
)

INDEX_FIELDS = (
    "schema_version",
    "applicant_ref",
    "authoritative_provider",
    "derived",
    "updated_at",
)


def canonical_profile(profile: dict) -> str:
    """A stable JSON string over the sorted entities plus the index (file-order free)."""
    entities = sorted(profile.get("entities", []), key=lambda e: e["id"])
    index = {k: v for k, v in profile.items() if k != "entities"}
    index["sources"] = sorted(index.get("sources", []), key=lambda s: s["source_id"])
    return json.dumps(
        {"index": index, "entities": entities},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def hash_profile(profile: dict) -> str:
    return hashlib.sha256(canonical_profile(profile).encode("utf-8")).hexdigest()


class Provider(ABC):
    """Storage for one ``CareerProfile`` (authoritative or derived)."""

    @abstractmethod
    def read(self) -> dict:
        """Return the stored profile, validated; refuse a too-new schema version."""

    @abstractmethod
    def write(self, profile: dict) -> str:
        """Persist ``profile`` atomically and return the new content hash."""

    def hash(self) -> str:
        return hash_profile(self.read())

    @abstractmethod
    def capabilities(self) -> dict:
        """Return ``{authoritative_ok, search, context}``."""

    @abstractmethod
    def export(self, target: dict) -> dict:
        """Write a derived copy to ``target`` and return a summary."""

    # --- ledgers ---

    @abstractmethod
    def append_source(self, source: dict) -> None:
        ...

    @abstractmethod
    def read_sources(self) -> list[dict]:
        ...

    @abstractmethod
    def store_diff(self, diff: dict) -> None:
        ...

    @abstractmethod
    def load_diff(self, diff_id: str) -> dict:
        ...

    @abstractmethod
    def append_approval(self, approval: dict) -> None:
        ...

    @abstractmethod
    def read_approvals(self) -> list[dict]:
        ...

    def find_approval(self, diff_id: str) -> dict | None:
        """The most recent approval for ``diff_id``, or None."""
        matches = [a for a in self.read_approvals() if a.get("diff_id") == diff_id]
        return matches[-1] if matches else None
