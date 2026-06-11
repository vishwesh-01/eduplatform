"""
assessment/__init__.py — Assessment Blueprint registration.
"""

from flask import Blueprint

assessment_bp = Blueprint("assessment", __name__)

from . import routes  # noqa: F401, E402
