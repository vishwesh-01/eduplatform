"""
certificates/services.py — PDF certificate generation using ReportLab.
"""

import logging
from io import BytesIO
from datetime import datetime, timezone

from reportlab.lib.pagesizes import landscape, letter
from reportlab.pdfgen import canvas as rl_canvas

logger = logging.getLogger(__name__)


def generate_certificate_pdf(
    learner_name: str,
    course_title: str,
    completion_date: str,
    cert_code: str,
) -> bytes:
    """
    Generate a professional PDF certificate and return it as bytes.

    Args:
        learner_name:     Full name of the learner (printed prominently).
        course_title:     Title of the completed course.
        completion_date:  Human-readable date string (e.g. "15 June 2025").
        cert_code:        UUID string used as the unique certificate identifier.

    Returns:
        PDF content as bytes, ready to stream in a Flask response.
    """
    buffer   = BytesIO()
    page_w, page_h = landscape(letter)  # 792 × 612 points
    c = rl_canvas.Canvas(buffer, pagesize=landscape(letter))

    center_x = page_w / 2

    # ── Outer decorative border ───────────────────────────────────────────
    c.setStrokeColorRGB(0.18, 0.36, 0.60)  # muted navy blue
    c.setLineWidth(3)
    c.rect(20, 20, page_w - 40, page_h - 40)

    # ── Inner decorative border ───────────────────────────────────────────
    c.setStrokeColorRGB(0.70, 0.80, 0.90)
    c.setLineWidth(1)
    c.rect(32, 32, page_w - 64, page_h - 64)

    # ── Platform name ─────────────────────────────────────────────────────
    c.setFillColorRGB(0.18, 0.36, 0.60)
    c.setFont("Helvetica-Bold", 13)
    c.drawCentredString(center_x, page_h - 70, "EduPlatform")

    # ── Horizontal rule under platform name ──────────────────────────────
    c.setStrokeColorRGB(0.18, 0.36, 0.60)
    c.setLineWidth(1)
    c.line(center_x - 120, page_h - 80, center_x + 120, page_h - 80)

    # ── Main heading ──────────────────────────────────────────────────────
    c.setFillColorRGB(0.12, 0.12, 0.12)
    c.setFont("Helvetica-Bold", 26)
    c.drawCentredString(center_x, page_h - 130, "CERTIFICATE OF COMPLETION")

    # ── Sub-heading ───────────────────────────────────────────────────────
    c.setFillColorRGB(0.35, 0.35, 0.35)
    c.setFont("Helvetica", 13)
    c.drawCentredString(center_x, page_h - 185, "This certifies that")

    # ── Learner name ──────────────────────────────────────────────────────
    c.setFillColorRGB(0.12, 0.12, 0.12)
    c.setFont("Helvetica-Bold", 32)
    c.drawCentredString(center_x, page_h - 240, learner_name)

    # ── Underline below name ──────────────────────────────────────────────
    name_w = c.stringWidth(learner_name, "Helvetica-Bold", 32)
    c.setStrokeColorRGB(0.60, 0.60, 0.60)
    c.setLineWidth(0.8)
    c.line(center_x - name_w / 2 - 10, page_h - 252,
           center_x + name_w / 2 + 10, page_h - 252)

    # ── Course label ──────────────────────────────────────────────────────
    c.setFillColorRGB(0.35, 0.35, 0.35)
    c.setFont("Helvetica", 13)
    c.drawCentredString(center_x, page_h - 290, "has successfully completed the course")

    # ── Course title ──────────────────────────────────────────────────────
    c.setFillColorRGB(0.18, 0.36, 0.60)
    c.setFont("Helvetica-BoldOblique", 20)
    c.drawCentredString(center_x, page_h - 330, course_title)

    # ── Completion date ───────────────────────────────────────────────────
    c.setFillColorRGB(0.35, 0.35, 0.35)
    c.setFont("Helvetica", 13)
    c.drawCentredString(center_x, page_h - 375, f"Completed on: {completion_date}")

    # ── Certificate UUID code ─────────────────────────────────────────────
    c.setFillColorRGB(0.50, 0.50, 0.50)
    c.setFont("Courier", 9)
    c.drawCentredString(center_x, 68, f"Certificate ID: {cert_code}")

    # ── Generated timestamp (authenticity marker) ─────────────────────────
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    c.setFont("Courier", 8)
    c.drawCentredString(center_x, 54, f"Generated: {ts}")

    c.save()
    buffer.seek(0)
    return buffer.read()
