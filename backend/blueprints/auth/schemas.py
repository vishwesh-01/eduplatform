"""
auth/schemas.py — Marshmallow schemas for auth request/response validation.
"""

import re
from marshmallow import Schema, ValidationError, fields, validate, validates


PASSWORD_REGEX = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$')


class RegisterSchema(Schema):
    """Validates the POST /auth/register request body."""
    name     = fields.Str(required=True, validate=validate.Length(min=2, max=200))
    email    = fields.Email(required=True)
    password = fields.Str(required=True, load_only=True)

    @validates("password")
    def validate_password(self, value):
        """Password must be 8+ chars with uppercase, lowercase, and a digit."""
        if not PASSWORD_REGEX.match(value):
            raise ValidationError(
                "Password must be at least 8 characters and contain at least "
                "one uppercase letter, one lowercase letter, and one digit."
            )


class LoginSchema(Schema):
    """Validates the POST /auth/login request body."""
    email    = fields.Email(required=True)
    password = fields.Str(required=True, load_only=True)


class TokenResponseSchema(Schema):
    """Shape of the token response returned on login/register."""
    access_token  = fields.Str()
    refresh_token = fields.Str()


class UserProfileSchema(Schema):
    """Serialises the user object returned after auth."""
    id         = fields.Str()
    name       = fields.Str()
    email      = fields.Str()
    skill_level = fields.Int(allow_none=True)
    goal_id    = fields.Str(allow_none=True)
    is_active  = fields.Bool()
    created_at = fields.DateTime()
