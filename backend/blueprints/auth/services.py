"""
auth/services.py — AuthService: business logic for registration, login,
                   token management, and RBAC helper decorators.
"""

import functools
import logging

import bcrypt
from flask import jsonify, g
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt,
    get_jwt_identity,
    verify_jwt_in_request,
)

from ...extensions import db
from ...models import Role, TokenBlocklist, User, UserRole

logger = logging.getLogger(__name__)


# ── Password helpers ─────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    """
    Hash a plain-text password with bcrypt.

    Args:
        plain: The plain-text password string.

    Returns:
        A bcrypt hash string (60 characters).
    """
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """
    Verify a plain-text password against a stored bcrypt hash.

    Args:
        plain:  Plain-text password to check.
        hashed: Previously hashed password from the database.

    Returns:
        True if the password matches; False otherwise.
    """
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


# ── Token helpers ─────────────────────────────────────────────────────────────

def issue_tokens(user_id: str) -> dict:
    """
    Create and return a new JWT access + refresh token pair.

    Args:
        user_id: The UUID string of the authenticated user.

    Returns:
        Dict with keys 'access_token' and 'refresh_token'.
    """
    return {
        "access_token":  create_access_token(identity=user_id),
        "refresh_token": create_refresh_token(identity=user_id),
    }


def revoke_token(jti: str) -> None:
    """
    Add a token's JTI to the blocklist so it cannot be used again.

    Args:
        jti: The JWT ID claim (string) to revoke.
    """
    db.session.add(TokenBlocklist(jti=jti))
    db.session.commit()


def is_token_revoked(jti: str) -> bool:
    """
    Check whether a token JTI is in the blocklist.

    Args:
        jti: JWT ID claim to check.

    Returns:
        True if revoked; False if still valid.
    """
    return db.session.get(TokenBlocklist, jti) is not None


# ── User helpers ──────────────────────────────────────────────────────────────

def get_user_roles(user: User) -> list[str]:
    """
    Return a list of role name strings for the given user.

    Args:
        user: SQLAlchemy User instance (with user_roles loaded).

    Returns:
        List of role names, e.g. ['student'].
    """
    return [ur.role.name for ur in user.user_roles]


def create_user(name: str, email: str, password: str) -> User:
    """
    Create a new user, hash their password, and assign the 'student' role.

    Args:
        name:     Display name.
        email:    Email address (must be unique).
        password: Plain-text password (already validated by schema).

    Returns:
        The persisted User instance.

    Raises:
        ValueError: If the email is already registered.
    """
    # Prevent duplicate emails
    if User.query.filter_by(email=email).first():
        raise ValueError("EMAIL_EXISTS")

    # Get the student role (must be seeded before this is called)
    student_role = Role.query.filter_by(name="student").first()
    if student_role is None:
        raise RuntimeError("student role not found — run seeds.py first")

    user = User(
        name=name,
        email=email,
        hashed_password=hash_password(password),
    )
    db.session.add(user)
    db.session.flush()  # get the user.id before adding user_role

    db.session.add(UserRole(user_id=user.id, role_id=student_role.id))
    db.session.commit()

    logger.info(f"New user registered: {user.id} ({email})")
    return user


# ── RBAC decorators ───────────────────────────────────────────────────────────

def require_role(*roles):
    """
    Decorator that restricts a route to users holding at least one of the
    specified roles.

    Usage:
        @require_role('admin')
        @require_role('student', 'admin')

    Returns HTTP 403 if the caller's role is not in the allowed set.
    """
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            user = db.session.get(User, user_id)

            if user is None or not user.is_active:
                from ...app import error_response
                return error_response(403, "FORBIDDEN", "Account not found or inactive.")

            user_roles = get_user_roles(user)
            if not any(r in user_roles for r in roles):
                from ...app import error_response
                return error_response(
                    403,
                    "FORBIDDEN",
                    f"This endpoint requires one of the following roles: {', '.join(roles)}.",
                )
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def own_resource(user_id_kwarg: str = "user_id"):
    """
    Decorator that ensures the authenticated user is accessing their own resource.

    Args:
        user_id_kwarg: The URL parameter name containing the target user's ID.

    Returns HTTP 403 if the JWT identity does not match the URL parameter.
    """
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            jwt_user_id = get_jwt_identity()
            resource_user_id = str(kwargs.get(user_id_kwarg, ""))
            if jwt_user_id != resource_user_id:
                from ...app import error_response
                return error_response(403, "FORBIDDEN", "You may only access your own resources.")
            return fn(*args, **kwargs)
        return wrapper
    return decorator
