"""Text-extraction check.

A rendered PDF must carry a real text layer (not an image), and that text must include the
content it was built from. pypdf extracts the text; the check fails if it is empty or if an
expected token is missing.
"""

from __future__ import annotations

from pathlib import Path


def extract_text(pdf_path) -> str:
    import pypdf

    reader = pypdf.PdfReader(str(Path(pdf_path)))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def check(pdf_path, expected_tokens=()) -> dict:
    text = extract_text(pdf_path)
    if not text.strip():
        return {"status": "fail", "details": "no extractable text (image-only PDF?)"}
    missing = [token for token in expected_tokens if token not in text]
    if missing:
        return {"status": "fail", "details": f"expected content missing: {missing}"}
    return {"status": "pass", "details": f"{len(text)} characters extracted"}
