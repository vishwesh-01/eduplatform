"""
models/learning_path.py — LearningPath and LearningPathItem models.

LearningPath: The personalised ordered course list generated for a learner.
LearningPathItem: A single course slot within a learning path, with position
                  and estimated_skill_gain populated by the LLM service.
"""

import uuid
from datetime import datetime, timezone

from ..extensions import db


class LearningPath(db.Model):
    """
    A personalised learning plan generated for a learner after assessment.
    One active path per (user, goal) pair — enforced by unique index.
    """

    __tablename__ = "learning_paths"

    __table_args__ = (
        db.Index(
            "idx_learning_paths_user_goal",
            "user_id",
            "goal_id",
            unique=True,
        ),
    )

    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    goal_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("goals.id", ondelete="RESTRICT"),
        nullable=False,
    )
    generated_at = db.Column(
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
    user = db.relationship("User", back_populates="learning_paths")
    goal = db.relationship("Goal", back_populates="learning_paths")
    items = db.relationship(
        "LearningPathItem",
        back_populates="path",
        cascade="all, delete-orphan",
        order_by="LearningPathItem.position",
    )

    def __repr__(self):
        return f"<LearningPath id={self.id} user={self.user_id}>"


class LearningPathItem(db.Model):
    """
    One course slot within a LearningPath.

    position: 1-based ordering of the course within the path.
    estimated_skill_gain: LLM-predicted % skill improvement for this course.
    """

    __tablename__ = "learning_path_items"

    __table_args__ = (
        db.Index("idx_lpi_path_id",   "path_id"),
        db.Index("idx_lpi_course_id", "course_id"),
        db.UniqueConstraint("path_id", "position", name="uq_lpi_path_position"),
    )

    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    path_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("learning_paths.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    course_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("courses.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    position = db.Column(db.SmallInteger, nullable=False)
    # Predicted skill improvement from completing this course (0-100)
    estimated_skill_gain = db.Column(db.Numeric(5, 2), nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # ── Relationships ────────────────────────────────────────────────────
    path   = db.relationship("LearningPath", back_populates="items")
    course = db.relationship("Course", back_populates="learning_path_items")

    def __repr__(self):
        return (
            f"<LearningPathItem path={self.path_id} "
            f"position={self.position} course={self.course_id}>"
        )
