"""
courses/__init__.py — Courses Blueprint registration.
Handles goals, courses, and learning path routes.
"""

from flask import Blueprint

courses_bp = Blueprint("courses", __name__)

from . import routes  # noqa: F401, E402
