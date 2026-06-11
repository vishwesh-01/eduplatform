"""
models/module.py — Module and UserModuleProgress models.

Module: A single lesson within a Course, optionally linked to a YouTube video.
UserModuleProgress: Records when a learner completes a specific module.
"""

import uuid
from datetime import datetime, timezone

from ..extensions import db


class Module(db.Model):
    """
    A discrete lesson unit within a Course.

    video_id, video_title, video_thumbnail_url are populated lazily by the
    YouTubeService on first fetch, then cached here to avoid repeated API calls.
    """

    __tablename__ = "modules"

    __table_args__ = (
        db.Index("idx_modules_course_id", "course_id"),
        db.UniqueConstraint("course_id", "position", name="uq_module_course_position"),
    )

    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = db.Column(db.String(300), nullable=False)
    # 1-based ordering within the parent course
    position = db.Column(db.SmallInteger, nullable=False)

    # YouTube metadata — cached on first fetch by YouTubeService
    video_id = db.Column(db.String(20), nullable=True)
    video_title = db.Column(db.String(500), nullable=True)
    video_thumbnail_url = db.Column(db.String(500), nullable=True)

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
    course = db.relationship("Course", back_populates="modules")
    user_progress = db.relationship(
        "UserModuleProgress", back_populates="module", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Module id={self.id} position={self.position} title={self.title!r}>"


class UserModuleProgress(db.Model):
    """
    Records a learner's completion of a single Module.
    Composite PK ensures one record per (user, module) pair (idempotent).
    """

    __tablename__ = "user_module_progress"

    __table_args__ = (
        db.Index("idx_ump_module_id", "module_id"),
    )

    user_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        primary_key=True,
    )
    module_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("modules.id", ondelete="CASCADE"),
        nullable=False,
        primary_key=True,
        index=True,
    )
    completed_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # ── Relationships ────────────────────────────────────────────────────
    user = db.relationship("User", back_populates="module_progress")
    module = db.relationship("Module", back_populates="user_progress")

    def __repr__(self):
        return f"<UserModuleProgress user={self.user_id} module={self.module_id}>"
