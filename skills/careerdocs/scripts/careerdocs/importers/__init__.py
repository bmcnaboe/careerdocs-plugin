"""Source importers.

Each importer turns one source file into a deterministic ``{"text_blocks", "candidates"}``
payload. Unstructured sources (DOCX, PDF, notes) yield text blocks for the agent to read
and no candidates; a structured source (a network/positions CSV) yields experience
candidates directly. The agent judges facts from the text blocks and writes the candidate
set; the CLI never invents qualifications.
"""

from __future__ import annotations

from pathlib import Path

from ..errors import CareerDocsError

KIND_BY_EXT = {
    ".docx": "resume_docx",
    ".pdf": "resume_pdf",
    ".csv": "network_export",
    ".md": "note",
    ".txt": "note",
}


def detect_kind(path) -> str | None:
    return KIND_BY_EXT.get(Path(path).suffix.lower())


def import_source(path, source_id: str) -> dict:
    ext = Path(path).suffix.lower()
    if ext == ".docx":
        from . import docx as module
    elif ext == ".pdf":
        from . import pdf as module
    elif ext == ".csv":
        from . import network_export as module
    elif ext in (".md", ".txt"):
        from . import note as module
    else:
        raise CareerDocsError(f"unsupported source type {ext!r}", code="USAGE")
    return module.extract(path, source_id)
