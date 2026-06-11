"""
models/user.py — User and UserRole models.

User: Platform learner or admin account.
UserRole: Many-to-many join between users and roles.
"""

import uuid
from datetime import datetime, timezone

from ..extensions import db


class UserRole(db.Model):
    """
    Association table linking users to roles (many-to-many).
    Composite primary key: (user_id, role_id).
    """

    __tablename__ = "user_roles"

    user_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        primary_key=True,
    )
    role_id = db.Column(
        db.Integer,
        db.ForeignKey("roles.id", ondelete="RESTRICT"),
        nullable=False,
        primary_key=True,
        index=True,
    )

    # ── Relationships ────────────────────────────────────────────────────
    user = db.relationship("User", back_populates="user_roles")
    role = db.relationship("Role", back_populates="user_roles")

    def __repr__(self):
        return f"<UserRole user_id={self.user_id} role_id={self.role_id}>"


class User(db.Model):
    """
    Platform user — either a learner (role='student') or administrator.

    skill_level is NULL until the learner completes a Diagnostic_Assessment.
    goal_id is NULL until the learner completes onboarding.
    """

    __tablename__ = "users"

    __table_args__ = (
        db.Index("idx_users_email", "email", unique=True),
        db.Index("idx_users_goal_id", "goal_id"),
        db.Index("idx_users_is_active", "is_active"),
        db.Index("idx_users_last_active", "last_active_at"),
    )

    id = db.Column(
        db.UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(254), nullable=False, unique=True)
    # bcrypt produces a 60-char hash; store as plain String (not LargeBinary)
    hashed_password = db.Column(db.String(60), nullable=False)

    # Assessed proficiency 0-100; NULL means not yet assessed
    skill_level = db.Column(db.SmallInteger, nullable=True)

    # FK to the learner's chosen career goal (set during onboarding)
    goal_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("goals.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    is_active = db.Column(db.Boolean, nullable=False, default=True)
    last_active_at = db.Column(db.DateTime(timezone=True), nullable=True)

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
    goal = db.relationship("Goal", back_populates="users")
    user_roles = db.relationship(
        "UserRole", back_populates="user", cascade="all, delete-orphan"
    )
    user_courses = db.relationship(
        "UserCourse", back_populates="user", cascade="all, delete-orphan"
    )
    module_progress = db.relationship(
        "UserModuleProgress", back_populates="user", cascade="all, delete-orphan"
    )
    quiz_sessions = db.relationship(
        "QuizSession", back_populates="user", cascade="all, delete-orphan"
    )
    learning_paths = db.relationship(
        "LearningPath", back_populates="user", cascade="all, delete-orphan"
    )
    certificates = db.relationship(
        "Certificate", back_populates="user", cascade="all, delete-orphan"
    )

    # ── Helper properties ────────────────────────────────────────────────

    @property
    def role_names(self):
        """Return list of role name strings for this user (e.g. ['student'])."""
        return [ur.role.name for ur in self.user_roles]

    def has_role(self, role_name: str) -> bool:
        """Return True if the user holds the given role."""
        return role_name in self.role_names

    def __repr__(self):
        return f"<User id={self.id} email={self.email!r}>"
