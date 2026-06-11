"""
auth/__init__.py — Auth Blueprint registration.

Exposes `auth_bp` which is imported by the app factory in app.py.
"""

from flask import Blueprint

auth_bp = Blueprint("auth", __name__)

# Import routes last to avoid circular imports
from . import routes  # noqa: F401, E402
