"""
models/goal.py — Goal model.

Represents a learner's career/learning objective (e.g. 'Python Developer').
Used to group courses, quiz questions, and learning paths.
"""

import uuid
from datetime import datetime, timezone

from ..extensions import db


class Goal(db.Model):
    """A learnable career goal offered by the platform."""

    __tablename__ = "goals"

    id = db.Column(
        db.UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name = db.Column(db.String(100), nullable=False, unique=True, index=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # ── Relationships ────────────────────────────────────────────────────
    courses = db.relationship("Course", back_populates="goal", lazy="dynamic")
    quiz_questions = db.relationship("QuizQuestion", back_populates="goal", lazy="dynamic")
    quiz_sessions = db.relationship("QuizSession", back_populates="goal", lazy="dynamic")
    learning_paths = db.relationship("LearningPath", back_populates="goal", lazy="dynamic")
    users = db.relationship("User", back_populates="goal", lazy="dynamic")

    def __repr__(self):
        return f"<Goal id={self.id} name={self.name!r}>"
