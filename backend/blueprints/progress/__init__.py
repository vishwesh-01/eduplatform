"""
progress/__init__.py — Progress Blueprint registration.
"""

from flask import Blueprint

progress_bp = Blueprint("progress", __name__)

from . import routes  # noqa: F401, E402
