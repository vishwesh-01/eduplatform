"""
assessment/schemas.py — Marshmallow schemas for the assessment engine.
"""

from marshmallow import Schema, fields, validate


class StartSessionSchema(Schema):
    """Validates POST /assessment/start body (no required fields — goal from user record)."""
    pass


class SubmitAnswerSchema(Schema):
    """Validates POST /assessment/answer body."""
    session_id      = fields.Str(required=True)
    question_id     = fields.Str(required=True)
    selected_option = fields.Int(required=True, validate=validate.Range(min=0, max=3))


class QuestionSchema(Schema):
    """Serialises one quiz question returned to the frontend."""
    id            = fields.Str()
    question_text = fields.Str()
    options       = fields.List(fields.Str())
    difficulty    = fields.Int()


class SessionSchema(Schema):
    """Serialises the current state of a quiz session (for resume)."""
    id                      = fields.Str()
    status                  = fields.Method("get_status")
    current_question_number = fields.Int()
    current_difficulty      = fields.Int()
    total_questions         = fields.Int()
    score                   = fields.Float(allow_none=True)
    started_at              = fields.DateTime()
    completed_at            = fields.DateTime(allow_none=True)

    def get_status(self, obj):
        return obj.status.value
