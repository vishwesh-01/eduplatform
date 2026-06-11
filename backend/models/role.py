"""
models/role.py — Role model.

Stores the two supported roles: 'student' and 'admin'.
Integer serial PK so role checks stay simple in RBAC decorators.
"""

from ..extensions import db


class Role(db.Model):
    """Lookup table for user roles."""

    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)

    # ── Relationships ────────────────────────────────────────────────────
    user_roles = db.relationship("UserRole", back_populates="role", lazy="dynamic")

    def __repr__(self):
        return f"<Role id={self.id} name={self.name!r}>"
