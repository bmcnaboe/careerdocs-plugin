"""Extract text blocks from a PDF resume (pdfplumber)."""

from __future__ import annotations

from pathlib import Path


def extract(path, source_id: str) -> dict:
    import pdfplumber

    blocks: list[str] = []
    with pdfplumber.open(str(Path(path))) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            blocks.extend(line.strip() for line in text.splitlines() if line.strip())
    return {"text_blocks": blocks, "candidates": []}
