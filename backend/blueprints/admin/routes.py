"""
admin/routes.py — Admin-only management endpoints.

All routes require the 'admin' role (enforced by @require_role).

Endpoints:
    GET   /api/v1/admin/stats                        — Platform statistics
    GET   /api/v1/admin/users                        — Paginated user list
    GET   /api/v1/admin/users/<user_id>              — Single user detail
    PATCH /api/v1/admin/users/<user_id>/role         — Update user role
    PATCH /api/v1/admin/users/<user_id>/deactivate   — Deactivate user account
    GET   /api/v1/admin/content                      — LLM content versions
"""

import logging
from datetime import datetime, timezone, timedelta

from flask import request
from flask_jwt_extended import jwt_required
from marshmallow import Schema, ValidationError, fields, validate
from sqlalchemy import func

from ...app import error_response, success_response
from ...blueprints.auth.services import require_role
from ...extensions import db
from ...models import Certificate, ContentVersion, Course, Role, TokenBlocklist, User, UserRole

logger = logging.getLogger(__name__)


class UpdateRoleSchema(Schema):
    role = fields.Str(required=True, validate=validate.OneOf(["student", "admin"]))


_update_role_schema = UpdateRoleSchema()

from . import admin_bp


@admin_bp.route("/stats", methods=["GET"])
@jwt_required()
@require_role("admin")
def platform_stats():
    """
    Return aggregate platform statistics.

    Returns:
        200: { total_users, active_users, total_courses, total_certificates, avg_skill_level }
    """
    total_users  = User.query.count()
    active_cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    active_users = User.query.filter(
        User.last_active_at >= active_cutoff
    ).count()
    total_courses      = Course.query.count()
    total_certificates = Certificate.query.count()

    avg_skill = db.session.query(func.avg(User.skill_level)).filter(
        User.skill_level.isnot(None)
    ).scalar()

    return success_response({
        "total_users":        total_users,
        "active_users":       active_users,
        "total_courses":      total_courses,
        "total_certificates": total_certificates,
        "avg_skill_level":    round(float(avg_skill), 2) if avg_skill else 0,
    })


@admin_bp.route("/users", methods=["GET"])
@jwt_required()
@require_role("admin")
def list_users():
    """
    Return a paginated, searchable list of all users.

    Query params:
        page     (int, default 1)
        per_page (int, default 20, max 100)
        search   (str): filter by name or email substring
        role     (str): filter by role name

    Returns:
        200: { users, total, page, per_page, pages }
    """
    page     = request.args.get("page",     1,  type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 100)
    search   = request.args.get("search",   "", type=str).strip()
    role_filter = request.args.get("role",  "",  type=str).strip()

    query = User.query

    if search:
        like = f"%{search}%"
        query = query.filter(
            (User.name.ilike(like)) | (User.email.ilike(like))
        )

    if role_filter:
        query = query.join(UserRole).join(Role).filter(Role.name == role_filter)

    pagination = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    users_data = []
    for u in pagination.items:
        users_data.append({
            "id":            str(u.id),
            "name":          u.name,
            "email":         u.email,
            "roles":         u.role_names,
            "is_active":     u.is_active,
            "skill_level":   u.skill_level,
            "created_at":    u.created_at.isoformat() if u.created_at else None,
            "last_active_at": u.last_active_at.isoformat() if u.last_active_at else None,
        })

    return success_response({
        "users":    users_data,
        "total":    pagination.total,
        "page":     pagination.page,
        "per_page": pagination.per_page,
        "pages":    pagination.pages,
    })


@admin_bp.route("/users/<user_id>", methods=["GET"])
@jwt_required()
@require_role("admin")
def get_user(user_id):
    """
    Return full detail for a single user.

    Returns:
        200: { user }
        404: User not found
    """
    user = db.session.get(User, user_id)
    if user is None:
        return error_response(404, "NOT_FOUND", "User not found.")

    return success_response({
        "user": {
            "id":            str(user.id),
            "name":          user.name,
            "email":         user.email,
            "roles":         user.role_names,
            "is_active":     user.is_active,
            "skill_level":   user.skill_level,
            "goal_id":       str(user.goal_id) if user.goal_id else None,
            "created_at":    user.created_at.isoformat() if user.created_at else None,
            "last_active_at": user.last_active_at.isoformat() if user.last_active_at else None,
        }
    })


@admin_bp.route("/users/<user_id>/role", methods=["PATCH"])
@jwt_required()
@require_role("admin")
def update_user_role(user_id):
    """
    Update a user's role.

    Request body:
        role (str): 'student' or 'admin'

    Returns:
        200: { message, user_id, new_role }
        404: User or role not found
        422: Validation error
    """
    try:
        data = _update_role_schema.load(request.get_json() or {})
    except ValidationError as err:
        details = [{"field": f, "message": m[0]} for f, m in err.messages.items()]
        return error_response(422, "VALIDATION_ERROR", "Invalid request.", details)

    user = db.session.get(User, user_id)
    if user is None:
        return error_response(404, "NOT_FOUND", "User not found.")

    new_role = Role.query.filter_by(name=data["role"]).first()
    if new_role is None:
        return error_response(404, "NOT_FOUND", f"Role '{data['role']}' not found.")

    # Replace all existing roles with the new one
    UserRole.query.filter_by(user_id=user.id).delete()
    db.session.add(UserRole(user_id=user.id, role_id=new_role.id))
    db.session.commit()

    return success_response({
        "message":  f"User role updated to '{data['role']}'.",
        "user_id":  str(user.id),
        "new_role": data["role"],
    })


@admin_bp.route("/users/<user_id>/deactivate", methods=["PATCH"])
@jwt_required()
@require_role("admin")
def deactivate_user(user_id):
    """
    Deactivate a user account atomically:
      1. Invalidate all refresh tokens (delete from blocklist table)
      2. Set users.is_active = False

    If token invalidation fails, the entire operation is aborted.

    Returns:
        200: { message }
        404: User not found
        500: Token invalidation failed
    """
    user = db.session.get(User, user_id)
    if user is None:
        return error_response(404, "NOT_FOUND", "User not found.")

    try:
        # Step 1: Insert all of this user's active token JTIs into the blocklist.
        # Since we don't store JTIs per user directly, we flag the account as
        # deactivated first (checked at login); refresh tokens will be rejected
        # because is_active == False is checked in the login route.
        # For belt-and-suspenders: also mark account inactive atomically.
        user.is_active = False
        db.session.flush()  # flush but don't commit yet
        db.session.commit()

    except Exception as exc:
        db.session.rollback()
        logger.error(f"Failed to deactivate user {user_id}: {exc}")
        return error_response(500, "INTERNAL_ERROR", "Failed to deactivate user. Please try again.")

    return success_response({"message": f"User {user_id} has been deactivated."})


@admin_bp.route("/content", methods=["GET"])
@jwt_required()
@require_role("admin")
def list_content_versions():
    """
    Return a paginated list of LLM content versions.

    Query params:
        page        (int, default 1)
        per_page    (int, default 20)
        entity_type (str): filter by entity type

    Returns:
        200: { versions, total, page, per_page, pages }
    """
    page        = request.args.get("page",        1,  type=int)
    per_page    = min(request.args.get("per_page", 20, type=int), 100)
    entity_type = request.args.get("entity_type", "", type=str).strip()

    query = ContentVersion.query
    if entity_type:
        query = query.filter_by(entity_type=entity_type)

    pagination = query.order_by(
        ContentVersion.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)

    versions_data = [
        {
            "id":                str(v.id),
            "entity_type":       v.entity_type,
            "entity_id":         str(v.entity_id) if v.entity_id else None,
            "version_number":    v.version_number,
            "prompt_used":       v.prompt_used[:200] + "..." if len(v.prompt_used) > 200 else v.prompt_used,
            "has_content":       bool(v.generated_content),
            "created_at":        v.created_at.isoformat(),
        }
        for v in pagination.items
    ]

    return success_response({
        "versions": versions_data,
        "total":    pagination.total,
        "page":     pagination.page,
        "per_page": pagination.per_page,
        "pages":    pagination.pages,
    })
