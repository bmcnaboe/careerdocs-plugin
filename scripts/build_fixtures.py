#!/usr/bin/env python3
"""Build the binary example fixtures deterministically.

The fictional applicant "Jordan Rivera" is sanitized (``example.com`` email, ``555``
phone) and lives entirely under ``examples/`` and ``tests/fixtures/``. This script builds
the artifacts that cannot be hand-authored — a DOCX resume (python-docx) and a PDF resume
(reportlab) — with fixed content and fixed metadata so re-running produces the same
documents. The two resumes deliberately disagree on one end date (the Globex role), which
is the conflict the onboarding flow must surface. Text fixtures (config, voice, notes,
CSV, job description, extracted candidates) are committed directly, not generated here.

Run: ``uv run --extra dev python scripts/build_fixtures.py``
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "examples" / "applicant" / "sources"

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


def main() -> None:
    build_resume_a_docx(SOURCES / "resume-a.docx")
    build_resume_b_pdf(SOURCES / "resume-b.pdf")
    print(f"built {SOURCES / 'resume-a.docx'}")
    print(f"built {SOURCES / 'resume-b.pdf'}")


if __name__ == "__main__":
    main()
