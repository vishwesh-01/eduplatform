"""
certificates/__init__.py — Certificates Blueprint registration.
"""

from flask import Blueprint

certificates_bp = Blueprint("certificates", __name__)

from . import routes  # noqa: F401, E402
