"""Stable identifiers: ``<type>_<ULID>``.

Every profile entity, source, and diff carries an immutable id: a type prefix, an
underscore, and a 26-character Crockford base32 ULID (48-bit millisecond timestamp plus
80 bits of randomness), so ids are unique, sortable by creation time, and free of the
ambiguous characters I, L, O, and U. Standard library only.
"""

from __future__ import annotations

import os
import re
import time

from .errors import CareerDocsError

# Crockford base32, excluding I, L, O, U (matches the schema's id pattern).
_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
_ULID_RE = re.compile(r"^[0-9A-HJKMNP-TV-Z]{26}$")

ENTITY_TYPES = (
    "contact",
    "experience",
    "achievement",
    "education",
    "skill",
    "project",
    "credential",
    "patent",
    "publication",
)
SOURCE_PREFIX = "src"
DIFF_PREFIX = "diff"
_NON_ENTITY_PREFIXES = (SOURCE_PREFIX, DIFF_PREFIX)


def _encode(value: int, length: int) -> str:
    chars = []
    for _ in range(length):
        chars.append(_ALPHABET[value & 0x1F])
        value >>= 5
    return "".join(reversed(chars))


def new_ulid(timestamp_ms: int | None = None) -> str:
    ts = (int(time.time() * 1000) if timestamp_ms is None else timestamp_ms) & ((1 << 48) - 1)
    randomness = int.from_bytes(os.urandom(10), "big")
    return _encode((ts << 80) | randomness, 26)


def is_valid_ulid(value: str) -> bool:
    return bool(_ULID_RE.match(value))


def new_id(entity_type: str) -> str:
    if entity_type not in ENTITY_TYPES:
        raise CareerDocsError(f"unknown entity type {entity_type!r}", code="USAGE")
    return f"{entity_type}_{new_ulid()}"


def new_source_id() -> str:
    return f"{SOURCE_PREFIX}_{new_ulid()}"


def new_diff_id() -> str:
    return f"{DIFF_PREFIX}_{new_ulid()}"


def parse_id(identifier: str, *, allowed_prefixes: tuple[str, ...] | None = None) -> tuple[str, str]:
    """Split ``<prefix>_<ULID>`` into ``(prefix, ulid)``; raise on a malformed id."""
    prefix, sep, ulid = identifier.partition("_")
    if not sep or not is_valid_ulid(ulid):
        raise CareerDocsError(f"malformed id {identifier!r}", code="USAGE")
    valid_prefixes = allowed_prefixes or (ENTITY_TYPES + _NON_ENTITY_PREFIXES)
    if prefix not in valid_prefixes:
        raise CareerDocsError(f"unknown id prefix {prefix!r} in {identifier!r}", code="USAGE")
    return prefix, ulid


def is_entity_id(identifier: str) -> bool:
    try:
        prefix, _ = parse_id(identifier, allowed_prefixes=ENTITY_TYPES)
    except CareerDocsError:
        return False
    return prefix in ENTITY_TYPES
