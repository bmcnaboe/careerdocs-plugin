"""Extract text blocks from a DOCX resume (python-docx)."""

from __future__ import annotations

from pathlib import Path


def extract(path, source_id: str) -> dict:
    from docx import Document  # top-level python-docx package

    document = Document(str(Path(path)))
    blocks = [p.text.strip() for p in document.paragraphs if p.text.strip()]
    return {"text_blocks": blocks, "candidates": []}
