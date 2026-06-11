"""
admin/__init__.py — Admin Blueprint registration.
"""

from flask import Blueprint

admin_bp = Blueprint("admin", __name__)

from . import routes  # noqa: F401, E402
