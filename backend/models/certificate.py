"""
models/certificate.py — Certificate model.

Issued automatically when a learner completes 100% of a course's modules.
certificate_code is a UUID used as both a unique identifier and the
verifiable code printed on the PDF.
"""

import uuid
from datetime import datetime, timezone

from ..extensions import db


class Certificate(db.Model):
    """
    A completion certificate earned by a learner for a specific course.
    certificate_code is a UUID stored as a unique string on the PDF document.
    """

    __tablename__ = "certificates"

    __table_args__ = (
        db.Index("idx_certificates_user_id",   "user_id"),
        db.Index("idx_certificates_course_id", "course_id"),
        db.Index("idx_certificates_code",      "certificate_code", unique=True),
    )

    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    course_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("courses.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    # Unique UUID printed on the certificate as a verifiable code
    certificate_code = db.Column(
        db.UUID(as_uuid=True),
        nullable=False,
        unique=True,
        default=uuid.uuid4,
    )
    issued_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # ── Relationships ────────────────────────────────────────────────────
    user   = db.relationship("User",   back_populates="certificates")
    course = db.relationship("Course", back_populates="certificates")

    def __repr__(self):
        return (
            f"<Certificate id={self.id} "
            f"user={self.user_id} course={self.course_id}>"
        )
