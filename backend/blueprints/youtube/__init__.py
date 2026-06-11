"""
youtube/__init__.py — YouTube Blueprint registration.
"""

from flask import Blueprint

youtube_bp = Blueprint("youtube", __name__)

from . import routes  # noqa: F401, E402
