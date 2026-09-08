"""Profile storage providers.

Exactly one provider is authoritative, selected by ``providers.authoritative`` in the
workspace config. The structured-Markdown provider is the reference implementation; the
Basic Memory provider writes the same entities as vault notes.
"""

from __future__ import annotations

from pathlib import Path

from .. import config as config_module
from ..errors import NotAuthoritative
from .base import Provider
from .markdown import MarkdownProvider

__all__ = ["Provider", "MarkdownProvider", "load_provider"]


def load_provider(workspace: str | Path, config: dict | None = None) -> Provider:
    """Return the authoritative provider for a workspace."""
    cfg = config if config is not None else config_module.resolve_config(workspace)
    name = cfg["providers"]["authoritative"]
    if name == "markdown":
        return MarkdownProvider(workspace, cfg)
    if name == "basic_memory":
        from .basic_memory import BasicMemoryProvider

        return BasicMemoryProvider(workspace, cfg)
    raise NotAuthoritative(f"unknown authoritative provider {name!r}")
