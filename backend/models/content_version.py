"""
models/content_version.py — ContentVersion model.

Every call to the Gemini API is persisted here, whether it succeeds or fails.
This enables audit, replay, and rollback of AI-generated content.
"""

import uuid
from datetime import datetime, timezone

from ..extensions import db


class ContentVersion(db.Model):
    """
    Immutable audit record of a single Gemini API call.

    entity_type:       Domain being generated (e.g. 'learning_path', 'quiz_question').
    entity_id:         UUID of the entity being created/updated (may be None for new).
    version_number:    Monotonically increasing integer per (entity_type, entity_id).
    prompt_used:       Exact prompt string sent to the model.
    generated_content: Parsed, validated JSON payload (empty dict on failure).
    raw_response:      Raw string returned by the API before parsing.
    """

    __tablename__ = "content_versions"

    __table_args__ = (
        db.Index("idx_cv_entity", "entity_type", "entity_id"),
    )

    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type = db.Column(db.String(50), nullable=False)
    # UUID of the entity this content was generated for; NULL for brand-new entities
    entity_id = db.Column(db.UUID(as_uuid=True), nullable=True)
    version_number = db.Column(db.Integer, nullable=False)
    prompt_used = db.Column(db.Text, nullable=False)
    # Validated structured content — stored as JSON; empty dict on LLM failure
    generated_content = db.Column(db.JSON, nullable=False, default=dict)
    # Raw string response from the API for debugging and replay
    raw_response = db.Column(db.Text, nullable=False, default="")
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self):
        return (
            f"<ContentVersion entity={self.entity_type}/{self.entity_id} "
            f"v{self.version_number}>"
        )
