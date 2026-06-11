"""
models/__init__.py — Import all ORM models so Alembic can discover them.

When Flask-Migrate generates or applies migrations, it inspects SQLAlchemy's
metadata. Every model must be imported here (even if not used directly) so
their table definitions are registered before `flask db migrate` runs.
"""

from .role import Role
from .goal import Goal
from .user import User, UserRole
from .course import Course, UserCourse
from .module import Module, UserModuleProgress
from .quiz import QuizAnswer, QuizQuestion, QuizSession
from .learning_path import LearningPath, LearningPathItem
from .certificate import Certificate
from .content_version import ContentVersion
from .token_blocklist import TokenBlocklist

__all__ = [
    "Role",
    "Goal",
    "User",
    "UserRole",
    "Course",
    "UserCourse",
    "Module",
    "UserModuleProgress",
    "QuizSession",
    "QuizQuestion",
    "QuizAnswer",
    "LearningPath",
    "LearningPathItem",
    "Certificate",
    "ContentVersion",
    "TokenBlocklist",
]
