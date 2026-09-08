"""Extract text blocks from a free-form note (Markdown or plain text)."""

from __future__ import annotations

from pathlib import Path


def extract(path, source_id: str) -> dict:
    text = Path(path).read_text(encoding="utf-8")
    blocks = [block.strip() for block in text.split("\n\n") if block.strip()]
    return {"text_blocks": blocks, "candidates": []}
