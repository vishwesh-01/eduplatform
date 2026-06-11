"""
auth/routes.py — HTTP route handlers for authentication.

Endpoints:
    POST /api/v1/auth/register  — Create account, return JWT tokens
    POST /api/v1/auth/login     — Verify credentials, return JWT tokens
    POST /api/v1/auth/logout    — Revoke refresh token
    POST /api/v1/auth/refresh   — Issue a new access token
    GET  /api/v1/auth/me        — Return current user's profile
"""

import logging

from flask import request
from flask_jwt_extended import (
    get_jwt,
    get_jwt_identity,
    jwt_required,
)
from marshmallow import ValidationError

from ...app import error_response, success_response
from ...extensions import db, limiter
from ...models import User
from . import auth_bp
from .schemas import LoginSchema, RegisterSchema, UserProfileSchema
from .services import (
    create_user,
    get_user_roles,
    is_token_revoked,
    issue_tokens,
    revoke_token,
    verify_password,
)

logger = logging.getLogger(__name__)

_register_schema = RegisterSchema()
_login_schema    = LoginSchema()
_profile_schema  = UserProfileSchema()


@auth_bp.route("/register", methods=["POST"])
@limiter.limit("5 per minute")
def register():
    """
    Register a new learner account.

    Request body:
        name     (str): Display name (2–200 chars)
        email    (str): Valid email address
        password (str): Min 8 chars, uppercase, lowercase, digit

    Returns:
        201: { access_token, refresh_token, user }
        409: Email already registered
        422: Validation errors
    """
    try:
        data = _register_schema.load(request.get_json() or {})
    except ValidationError as err:
        details = [{"field": f, "message": m[0]} for f, m in err.messages.items()]
        return error_response(422, "VALIDATION_ERROR", "Request body failed validation.", details)

    try:
        user = create_user(data["name"], data["email"], data["password"])
    except ValueError:
        return error_response(409, "EMAIL_EXISTS", "This email is already registered.")

    tokens = issue_tokens(str(user.id))
    return success_response({**tokens, "user": _profile_schema.dump(user)}, status=201)


@auth_bp.route("/login", methods=["POST"])
@limiter.limit("10 per minute")
def login():
    """
    Authenticate a user and return JWT tokens.

    Request body:
        email    (str)
        password (str)

    Returns:
        200: { access_token, refresh_token, user }
        401: Invalid credentials
        422: Validation errors
    """
    try:
        data = _login_schema.load(request.get_json() or {})
    except ValidationError as err:
        details = [{"field": f, "message": m[0]} for f, m in err.messages.items()]
        return error_response(422, "VALIDATION_ERROR", "Request body failed validation.", details)

    user = User.query.filter_by(email=data["email"]).first()

    if user is None or not verify_password(data["password"], user.hashed_password):
        return error_response(401, "UNAUTHORIZED", "Invalid email or password.")

    if not user.is_active:
        return error_response(403, "FORBIDDEN", "This account has been deactivated.")

    # Update last active timestamp
    from datetime import datetime, timezone
    user.last_active_at = datetime.now(timezone.utc)
    db.session.commit()

    tokens = issue_tokens(str(user.id))
    return success_response({**tokens, "user": _profile_schema.dump(user)})


@auth_bp.route("/logout", methods=["POST"])
@jwt_required(refresh=True)
def logout():
    """
    Revoke the caller's refresh token (add its JTI to the blocklist).

    Requires: Authorization: Bearer <refresh_token>

    Returns:
        200: Logged out successfully
    """
    jti = get_jwt()["jti"]
    revoke_token(jti)
    return success_response({"message": "Successfully logged out."})


@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    """
    Issue a new short-lived access token using a valid refresh token.

    Requires: Authorization: Bearer <refresh_token>

    Returns:
        200: { access_token }
        401: Token expired or revoked
    """
    jti = get_jwt()["jti"]
    if is_token_revoked(jti):
        return error_response(401, "TOKEN_REVOKED", "This refresh token has been revoked.")

    user_id = get_jwt_identity()
    from flask_jwt_extended import create_access_token
    new_token = create_access_token(identity=user_id)
    return success_response({"access_token": new_token})


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    """
    Return the currently authenticated user's profile.

    Returns:
        200: { user }
        404: User not found
    """
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)
    if user is None:
        return error_response(404, "NOT_FOUND", "User not found.")
    return success_response({"user": _profile_schema.dump(user)})


@auth_bp.route("/profile", methods=["PATCH"])
@jwt_required()
def update_profile():
    """
    Update the authenticated user's name and/or email.

    Request body:
        name  (str, optional)
        email (str, optional)

    Returns:
        200: { user }
        409: Email taken by another account
    """
    from marshmallow import Schema, fields as mf
    from ...models import User as _User

    class ProfileSchema(Schema):
        name  = mf.Str(validate=lambda v: 2 <= len(v.strip()) <= 200)
        email = mf.Email()

    try:
        data = ProfileSchema().load(request.get_json() or {})
    except Exception as err:
        return error_response(422, "VALIDATION_ERROR", str(err))

    user_id = get_jwt_identity()
    user = db.session.get(_User, user_id)
    if user is None:
        return error_response(404, "NOT_FOUND", "User not found.")

    if "email" in data and data["email"] != user.email:
        if _User.query.filter_by(email=data["email"]).first():
            return error_response(409, "EMAIL_EXISTS", "This email is already in use.")
        user.email = data["email"]

    if "name" in data:
        user.name = data["name"].strip()

    db.session.commit()
    return success_response({"user": _profile_schema.dump(user)})
