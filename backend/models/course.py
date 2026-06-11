"""
models/course.py — Course and UserCourse models.

Course: A structured learning unit belonging to a goal, containing modules.
UserCourse: Tracks a learner's enrolment and completion progress per course.
"""

import uuid
from datetime import datetime, timezone

from ..extensions import db


class Course(db.Model):
    """
    A course offered for a specific learning goal.
    Contains an ordered list of Module objects.
    """

    __tablename__ = "courses"

    __table_args__ = (
        db.Index("idx_courses_goal_id", "goal_id"),
        db.Index("idx_courses_title", "title"),
    )

    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    goal_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("goals.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    title = db.Column(db.String(300), nullable=False)
    instructor = db.Column(db.String(200), nullable=True)
    # Estimated duration in fractional hours (e.g. 12.50)
    duration_hours = db.Column(db.Numeric(5, 2), nullable=True)

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
    goal = db.relationship("Goal", back_populates="courses")
    modules = db.relationship(
        "Module",
        back_populates="course",
        cascade="all, delete-orphan",
        order_by="Module.position",
    )
    user_courses = db.relationship(
        "UserCourse", back_populates="course", cascade="all, delete-orphan"
    )
    learning_path_items = db.relationship(
        "LearningPathItem", back_populates="course"
    )
    certificates = db.relationship("Certificate", back_populates="course")

    def __repr__(self):
        return f"<Course id={self.id} title={self.title!r}>"


class UserCourse(db.Model):
    """
    Tracks a learner's enrolment in and progress through a course.
    Composite PK: (user_id, course_id).
    """

    __tablename__ = "user_courses"

    __table_args__ = (
        db.Index("idx_user_courses_course_id", "course_id"),
        db.Index("idx_user_courses_completed", "completed_at"),
    )

    user_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        primary_key=True,
    )
    course_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        primary_key=True,
        index=True,
    )
    enrolled_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    # Percentage 0.00–100.00; recalculated on each module completion
    completion_percentage = db.Column(
        db.Numeric(5, 2), nullable=False, default=0.00
    )
    # Set when completion_percentage reaches 100
    completed_at = db.Column(db.DateTime(timezone=True), nullable=True)

    # ── Relationships ────────────────────────────────────────────────────
    user = db.relationship("User", back_populates="user_courses")
    course = db.relationship("Course", back_populates="user_courses")

    def __repr__(self):
        return (
            f"<UserCourse user={self.user_id} course={self.course_id} "
            f"pct={self.completion_percentage}>"
        )
