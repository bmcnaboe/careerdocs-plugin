"""Profile storage: the structured-Markdown provider.

``providers.authoritative`` in the workspace config names the provider; ``markdown`` is
the only one.
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
    raise NotAuthoritative(f"unknown authoritative provider {name!r}")
