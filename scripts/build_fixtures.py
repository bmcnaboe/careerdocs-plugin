#!/usr/bin/env python3
"""Build the binary example fixtures deterministically.

The fictional applicant "Jordan Rivera" is sanitized (``example.com`` email, ``555``
phone) and lives entirely under ``examples/`` and ``tests/fixtures/``. This script builds
the artifacts that cannot be hand-authored — a DOCX resume (python-docx) and a PDF resume
(reportlab) — with fixed content and fixed metadata so re-running produces the same
documents. The two resumes deliberately disagree on one end date (the Globex role), which
is the conflict the onboarding flow must surface. Text fixtures (config, voice, notes,
CSV, job description, extracted candidates) are committed directly, not generated here.

Run: ``uv run --extra dev python scripts/build_fixtures.py`` (``--templates-only`` rebuilds
just the two example templates).
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "examples" / "applicant" / "sources"
TEMPLATES = ROOT / "examples" / "applicant" / "templates"
RENDERED = ROOT / "tests" / "fixtures" / "rendered"

FIXED_TIME = datetime(2024, 1, 1, 0, 0, 0)

CONTACT = {
    "name": "Jordan Rivera",
    "headline": "Engineering Leader",
    "location": "Metropolis, USA",
    "email": "jordan.rivera@example.com",
    "phone": "(555) 555-0142",
}

# The Globex end date is the deliberate conflict: the DOCX says 2021-06, the PDF 2021-08.
GLOBEX_END_DOCX = "June 2021"
GLOBEX_END_PDF = "August 2021"

ACHIEVEMENTS = [
    "Grew the platform engineering team from 4 to 15 engineers.",
    "Cut cloud infrastructure costs by 35% through workload consolidation.",
]
SKILLS = ["Python", "Go", "Kubernetes", "Team Leadership"]


def build_resume_a_docx(path: Path) -> None:
    from docx import Document

    document = Document()
    document.add_heading(CONTACT["name"], level=0)
    document.add_paragraph(f"{CONTACT['headline']} — {CONTACT['location']}")
    document.add_paragraph(f"{CONTACT['email']} · {CONTACT['phone']}")

    document.add_heading("Experience", level=1)
    document.add_heading(f"Engineering Manager, Globex Corporation", level=2)
    document.add_paragraph(f"March 2018 – {GLOBEX_END_DOCX}")
    for achievement in ACHIEVEMENTS:
        document.add_paragraph(achievement, style="List Bullet")

    document.add_heading("Senior Software Engineer, Initech", level=2)
    document.add_paragraph("January 2015 – February 2018")
    document.add_paragraph("Built and operated the billing platform.", style="List Bullet")

    document.add_heading("Skills", level=1)
    document.add_paragraph(", ".join(SKILLS))

    document.add_heading("Education", level=1)
    document.add_paragraph("B.S. Computer Science, State University (2011 – 2015)")

    props = document.core_properties
    props.created = FIXED_TIME
    props.modified = FIXED_TIME
    props.author = CONTACT["name"]

    path.parent.mkdir(parents=True, exist_ok=True)
    document.save(str(path))


def build_resume_b_pdf(path: Path) -> None:
    from reportlab import rl_config

    rl_config.invariant = 1  # deterministic timestamps and ids
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    path.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(path), pagesize=letter, invariant=1)
    width, height = letter
    y = height - 72

    def line(text: str, size: int = 11, gap: int = 16) -> None:
        nonlocal y
        pdf.setFont("Helvetica", size)
        pdf.drawString(72, y, text)
        y -= gap

    line(CONTACT["name"], size=18, gap=24)
    line(f"{CONTACT['headline']} — {CONTACT['location']}")
    line(f"{CONTACT['email']} · {CONTACT['phone']}", gap=24)

    line("Experience", size=14, gap=20)
    line("Engineering Manager, Globex Corporation")
    line(f"March 2018 – {GLOBEX_END_PDF}", gap=20)
    line("Senior Software Engineer, Initech")
    line("January 2015 – February 2018", gap=24)

    line("Skills", size=14, gap=20)
    line(", ".join(SKILLS))

    pdf.setTitle("Jordan Rivera — Resume")
    pdf.setAuthor(CONTACT["name"])
    pdf.showPage()
    pdf.save()


RESUME_TEMPLATE_JSON = {
    "name": "example-resume",
    "kind": "resume",
    "version": "1",
    "page_budget": 2,
    "units_per_page": 12,
    "sections": [
        {"id": "header", "title": "", "placeholder": "contact", "entity_types": ["contact"], "max_items": 1, "required": True},
        {"id": "experience", "title": "Experience", "placeholder": "experience", "entity_types": ["experience", "achievement"], "max_items": 12, "required": True, "role_summaries": True},
        {"id": "projects", "title": "Projects", "placeholder": "projects", "entity_types": ["project"], "max_items": 6, "required": False},
        {"id": "skills", "title": "Skills", "placeholder": "skills", "entity_types": ["skill"], "max_items": 20, "required": False},
        {"id": "education", "title": "Education", "placeholder": "education", "entity_types": ["education"], "max_items": 5, "required": False},
    ],
    "allowlist": ["Experience", "Projects", "Skills", "Education"],
    "style_notes": "Two-page budget; verb-first bullets; no buzzwords. Single column, centered name, ruled headings, right-tab dates.",
}

COVER_LETTER_TEMPLATE_JSON = {
    "name": "example-cover-letter",
    "kind": "cover_letter",
    "version": "1",
    "page_budget": 1,
    "units_per_page": 6,
    "sections": [
        {"id": "header", "title": "", "placeholder": "contact", "entity_types": ["contact"], "max_items": 1, "required": True},
        {"id": "body", "title": "", "placeholder": "body", "kind": "sentence", "entity_types": ["experience", "skill"], "max_items": 6, "required": True},
    ],
    "allowlist": ["Sincerely,"],
    "style_notes": "One page; complements the resume; draft prose in voice, never paste resume bullets. The greeting is the first body unit; the template carries the sign-off.",
}


_INK = "1F1F1F"
_MARGIN_INCHES = 0.7
_TEXT_WIDTH_INCHES = 8.5 - 2 * _MARGIN_INCHES


def _base_document():
    """Letter page, 0.7-inch margins, Calibri 10.5 pt body in near-black."""
    from docx import Document
    from docx.oxml.ns import qn
    from docx.shared import Inches, Pt, RGBColor

    document = Document()
    section = document.sections[0]
    section.page_width, section.page_height = Inches(8.5), Inches(11)
    for margin in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
        setattr(section, margin, Inches(_MARGIN_INCHES))
    normal = document.styles["Normal"]
    normal.font.name, normal.font.size = "Calibri", Pt(10.5)
    normal.font.color.rgb = RGBColor.from_string(_INK)
    normal.element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")
    normal.paragraph_format.space_before = Pt(0)
    normal.paragraph_format.space_after = Pt(0)
    normal.paragraph_format.line_spacing = 1.0
    return document


def _paragraph(document, text=None, *, size=None, bold=None, center=False, before=None,
               after=None, style=None, caps=False):
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Pt

    paragraph = document.add_paragraph(style=style)
    if center:
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if before is not None:
        paragraph.paragraph_format.space_before = Pt(before)
    if after is not None:
        paragraph.paragraph_format.space_after = Pt(after)
    if text is not None:
        run = paragraph.add_run(text)
        if size:
            run.font.size = Pt(size)
        if bold is not None:
            run.bold = bold
        if caps:
            run.font.all_caps = True  # displayed in capitals; the text itself stays as written
    return paragraph


def _rule_below(paragraph) -> None:
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn

    border = OxmlElement("w:bottom")
    for attribute, value in (("w:val", "single"), ("w:sz", "6"), ("w:space", "1"), ("w:color", _INK)):
        border.set(qn(attribute), value)
    borders = OxmlElement("w:pBdr")
    borders.append(border)
    paragraph._p.get_or_add_pPr().append(borders)


def _preserve_spaces(document) -> None:
    # Rendered values may begin or end with a space; keep every text run intact.
    from docx.oxml.ns import qn

    for text in document.element.body.iter(qn("w:t")):
        text.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")


def _header(document, *, after: float) -> None:
    _paragraph(document, "{{ contact_name }}", size=20, bold=True, center=True, after=2)
    _paragraph(document, "{{ contact_details }}", size=10, center=True, after=after)


def _finish(document, directory: Path, manifest: dict) -> None:
    _preserve_spaces(document)
    props = document.core_properties
    props.created = FIXED_TIME
    props.modified = FIXED_TIME
    directory.mkdir(parents=True, exist_ok=True)
    document.save(str(directory / "template.docx"))
    (directory / "template.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def build_resume_template(directory: Path) -> None:
    """Single column: centered name and contact line, ruled uppercase section headings,
    bold role lines with the dates on a right tab stop and the role's summary beneath,
    bulleted achievements."""
    from docx.enum.text import WD_TAB_ALIGNMENT
    from docx.shared import Inches, Pt

    document = _base_document()
    _header(document, after=3)
    _paragraph(document, "{%p for section in sections %}")
    _paragraph(document, "{%p if section.units %}")
    _rule_below(_paragraph(document, "{{ section.title }}", size=11, bold=True, before=10, after=3.5, caps=True))
    _paragraph(document, "{%p for unit in section.units %}")
    _paragraph(document, "{%p if unit.kind == 'bullet' %}")
    _paragraph(document, "{{ unit.text }}", style="List Bullet", after=2)
    _paragraph(document, "{%p elif section.id == 'experience' %}")
    role = _paragraph(document, before=6, after=1)
    role.paragraph_format.tab_stops.add_tab_stop(Inches(_TEXT_WIDTH_INCHES), WD_TAB_ALIGNMENT.RIGHT)
    run = role.add_run("{{ unit.head }}")
    run.bold, run.font.size = True, Pt(11)
    role.add_run().add_tab()
    role.add_run("{{ unit.tail }}")
    _paragraph(document, "{%p if unit.note %}")
    _paragraph(document, "{{ unit.note }}", after=1)
    _paragraph(document, "{%p endif %}")
    _paragraph(document, "{%p else %}")
    _paragraph(document, "{{ unit.text }}", after=2)
    _paragraph(document, "{%p endif %}")
    _paragraph(document, "{%p endfor %}")
    _paragraph(document, "{%p endif %}")
    _paragraph(document, "{%p endfor %}")
    _finish(document, directory, RESUME_TEMPLATE_JSON)


def build_cover_letter_template(directory: Path) -> None:
    """The same header, body paragraphs, and a sign-off followed by the name."""
    document = _base_document()
    _header(document, after=16)
    _paragraph(document, "{%p for section in sections %}")
    _paragraph(document, "{%p for unit in section.units %}")
    _paragraph(document, "{{ unit.text }}", size=11, after=8)
    _paragraph(document, "{%p endfor %}")
    _paragraph(document, "{%p endfor %}")
    _paragraph(document, "Sincerely,", size=11, before=2, after=14)
    _paragraph(document, "{{ contact_name }}", size=11)
    _finish(document, directory, COVER_LETTER_TEMPLATE_JSON)


_RESUME_LINES = [
    ("Jordan Rivera", 18, 26),
    ("Engineering Leader — Metropolis, USA", 11, 16),
    ("jordan.rivera@example.com · (555) 555-0142", 11, 24),
    ("Experience", 14, 20),
    ("Engineering Manager, Globex Corporation (2018-03–2021-06)", 11, 16),
    ("Grew the platform engineering team from 4 to 15 engineers.", 11, 16),
    ("Cut cloud infrastructure costs by 35% through workload consolidation.", 11, 24),
    ("Senior Software Engineer, Initech (2015-01–2018-02)", 11, 24),
    ("Skills", 14, 20),
    ("Python, Go, Kubernetes, Team Leadership", 11, 24),
    ("Education", 14, 20),
    ("B.S. Computer Science, State University", 11, 16),
]


def build_example_resume_pdf(path: Path) -> None:
    """A representative rendered resume PDF for the layout checks, with 1-inch margins."""
    from reportlab import rl_config

    rl_config.invariant = 1
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    path.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(path), pagesize=letter, invariant=1)
    _width, height = letter
    y = height - 72  # 1-inch top margin
    for text, size, gap in _RESUME_LINES:
        pdf.setFont("Helvetica-Bold" if size >= 14 else "Helvetica", size)
        pdf.drawString(72, y, text)  # 1-inch left margin
        y -= gap
    pdf.setTitle("Jordan Rivera — Resume")
    pdf.showPage()
    pdf.save()


def main(argv: list[str] | None = None) -> None:
    templates_only = "--templates-only" in (argv if argv is not None else sys.argv[1:])
    if not templates_only:
        build_resume_a_docx(SOURCES / "resume-a.docx")
        build_resume_b_pdf(SOURCES / "resume-b.pdf")
        build_example_resume_pdf(RENDERED / "example-resume.pdf")
        print(f"built {SOURCES / 'resume-a.docx'}")
        print(f"built {SOURCES / 'resume-b.pdf'}")
        print(f"built {RENDERED / 'example-resume.pdf'}")
    build_resume_template(TEMPLATES / "resume")
    build_cover_letter_template(TEMPLATES / "cover-letter")
    print(f"built {TEMPLATES / 'resume' / 'template.docx'}")
    print(f"built {TEMPLATES / 'cover-letter' / 'template.docx'}")


if __name__ == "__main__":
    main()
