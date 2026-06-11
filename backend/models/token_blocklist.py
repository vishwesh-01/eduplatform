"""
models/token_blocklist.py — TokenBlocklist model.

Stores the JTI (JWT ID) of revoked refresh tokens so they cannot be reused
after logout or account deactivation.

Periodic cleanup: rows older than 7 days (the max refresh token lifetime)
can be safely deleted via a scheduled job:
    DELETE FROM token_blocklist WHERE created_at < NOW() - INTERVAL '7 days'
"""

from datetime import datetime, timezone

from ..extensions import db


class TokenBlocklist(db.Model):
    """
    Revoked JWT refresh token registry.
    Primary key is the JTI claim from the JWT (a UUID string, 36 chars).
    """

    __tablename__ = "token_blocklist"

    __table_args__ = (
        # Index supports efficient cleanup of expired rows
        db.Index("idx_token_blocklist_created", "created_at"),
    )

    # JTI is a UUID string like "f47ac10b-58cc-4372-a567-0e02b2c3d479"
    jti = db.Column(db.String(36), primary_key=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self):
        return f"<TokenBlocklist jti={self.jti!r}>"
