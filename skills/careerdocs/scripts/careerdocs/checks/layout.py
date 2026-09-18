"""Rendered-layout check.

pdfplumber inspects each page: content must stay inside the margins and not exceed a
sane text density (a proxy for an overfull page), and any line the template expects on
one line (the contact details) must not have wrapped. pypdfium2 renders one PNG per page
so a human or the acceptance phase can eyeball the result.
"""

from __future__ import annotations

from pathlib import Path

_DEFAULT_MARGIN_PTS = 36  # 0.5 inch
_MAX_CHARS_PER_PAGE = 6000


def render_page_pngs(pdf_path, out_dir: Path, name: str, scale: float = 1.0) -> list[Path]:
    import pypdfium2 as pdfium

    out_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    pdf = pdfium.PdfDocument(str(Path(pdf_path)))
    try:
        for index in range(len(pdf)):
            image = pdf[index].render(scale=scale).to_pil()
            png_path = out_dir / f"{name}-p{index + 1}.png"
            image.save(png_path)
            paths.append(png_path)
    finally:
        pdf.close()
    return paths


def _squash(text: str) -> str:
    return " ".join(text.split())


def check(pdf_path, out_dir: Path | None = None, name: str = "layout", margin: float = _DEFAULT_MARGIN_PTS,
          single_lines=()) -> dict:
    """``single_lines`` are strings that must each render as one line of the PDF."""
    import pdfplumber

    findings: list[str] = []
    rendered_lines: set[str] = set()
    with pdfplumber.open(str(Path(pdf_path))) as pdf:
        for page_no, page in enumerate(pdf.pages, start=1):
            rendered_lines.update(_squash(line) for line in (page.extract_text() or "").splitlines())
            chars = page.chars
            if not chars:
                continue
            if min(c["x0"] for c in chars) < margin:
                findings.append(f"page {page_no}: content past the left margin")
            if max(c["x1"] for c in chars) > page.width - margin:
                findings.append(f"page {page_no}: content past the right margin")
            if min(c["top"] for c in chars) < margin:
                findings.append(f"page {page_no}: content above the top margin")
            if max(c["bottom"] for c in chars) > page.height - margin:
                findings.append(f"page {page_no}: content below the bottom margin")
            if len(chars) > _MAX_CHARS_PER_PAGE:
                findings.append(f"page {page_no}: text density too high ({len(chars)} chars)")
    for line in single_lines:
        if _squash(line) and _squash(line) not in rendered_lines:
            findings.append(f"wrapped line: {line!r} does not fit on one line; shorten it")

    pngs: list[Path] = []
    if out_dir is not None:
        pngs = render_page_pngs(pdf_path, out_dir, name)

    if findings:
        return {"status": "fail", "details": "; ".join(findings)}
    detail = "margins and density within bounds"
    if pngs:
        detail += f"; {len(pngs)} page render(s)"
    return {"status": "pass", "details": detail}
