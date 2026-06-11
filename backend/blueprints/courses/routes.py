"""
courses/routes.py — Endpoints for goals, courses, and learning paths.

Endpoints:
    GET  /api/v1/goals              — List all learning goals
    POST /api/v1/goals/select       — Set the authenticated learner's goal
    GET  /api/v1/courses            — List courses for the learner's goal (paginated)
    GET  /api/v1/courses/<course_id> — Course detail with modules
    GET  /api/v1/learning-path      — Current learner's active learning path
    GET  /api/v1/learning-path/<id> — Specific learning path by ID
"""

import logging

from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from marshmallow import ValidationError

from ...app import error_response, success_response
from ...extensions import db
from ...models import Course, Goal, LearningPath, User
from . import courses_bp
from .schemas import (
    CourseDetailSchema,
    CourseSchema,
    GoalSchema,
    LearningPathSchema,
    SelectGoalSchema,
)

logger = logging.getLogger(__name__)

_goal_schema         = GoalSchema(many=True)
_course_schema       = CourseSchema(many=True)
_course_detail_schema = CourseDetailSchema()
_learning_path_schema = LearningPathSchema()
_select_goal_schema  = SelectGoalSchema()


# ── Goals ─────────────────────────────────────────────────────────────────────

@courses_bp.route("/goals", methods=["GET"])
@jwt_required()
def list_goals():
    """
    Return all available learning goals.

    Returns:
        200: { goals: [...] }
    """
    goals = Goal.query.order_by(Goal.name).all()
    return success_response({"goals": _goal_schema.dump(goals)})


@courses_bp.route("/goals/select", methods=["POST"])
@jwt_required()
def select_goal():
    """
    Persist the learner's chosen learning goal.

    Request body:
        goal_id (str): UUID of the chosen Goal

    Returns:
        200: { message, goal_id }
        404: Goal not found
        422: Validation error
    """
    try:
        data = _select_goal_schema.load(request.get_json() or {})
    except ValidationError as err:
        details = [{"field": f, "message": m[0]} for f, m in err.messages.items()]
        return error_response(422, "VALIDATION_ERROR", "Invalid request body.", details)

    goal = db.session.get(Goal, data["goal_id"])
    if goal is None:
        return error_response(404, "NOT_FOUND", "Goal not found.")

    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)
    if user is None:
        return error_response(404, "NOT_FOUND", "User not found.")

    user.goal_id = goal.id
    db.session.commit()

    return success_response({"message": f"Goal set to '{goal.name}'.", "goal_id": str(goal.id)})


# ── Courses ───────────────────────────────────────────────────────────────────

@courses_bp.route("/courses", methods=["GET"])
@jwt_required()
def list_courses():
    """
    Return a paginated list of courses for the authenticated learner's goal.

    Query params:
        page     (int, default 1)
        per_page (int, default 10, max 50)

    Returns:
        200: { courses, total, page, per_page, pages }
    """
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)

    if user is None or user.goal_id is None:
        return error_response(400, "NO_GOAL", "Please complete onboarding and select a learning goal first.")

    page     = request.args.get("page",     1,  type=int)
    per_page = min(request.args.get("per_page", 10, type=int), 50)

    pagination = (
        Course.query
        .filter_by(goal_id=user.goal_id)
        .order_by(Course.title)
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    return success_response({
        "courses":  _course_schema.dump(pagination.items),
        "total":    pagination.total,
        "page":     pagination.page,
        "per_page": pagination.per_page,
        "pages":    pagination.pages,
    })


@courses_bp.route("/courses/<course_id>", methods=["GET"])
@jwt_required()
def get_course(course_id):
    """
    Return full course detail including ordered modules with YouTube metadata.

    Path param:
        course_id (str): UUID of the Course

    Returns:
        200: { course }
        404: Course not found
    """
    course = db.session.get(Course, course_id)
    if course is None:
        return error_response(404, "NOT_FOUND", "Course not found.")

    # Auto-fetch YouTube metadata for any module missing a video_id
    _auto_fetch_youtube(course)

    return success_response({"course": _course_detail_schema.dump(course)})


def _auto_fetch_youtube(course):
    """
    For each module in the course that lacks a cached video_id, query the
    YouTubeService to fetch and persist metadata. Errors are swallowed so a
    YouTube API failure does not block the course detail response.
    """
    try:
        from ..youtube.services import YouTubeService
        yt = YouTubeService()
        for module in course.modules:
            if module.video_id is None:
                query = f"{course.title} {module.title}"
                meta = yt.fetch_video_metadata(query)
                if meta:
                    module.video_id            = meta.get("video_id")
                    module.video_title         = meta.get("title")
                    module.video_thumbnail_url = meta.get("thumbnail_url")
        db.session.commit()
    except Exception as exc:
        logger.warning(f"YouTube auto-fetch skipped: {exc}")


# ── Learning Path ─────────────────────────────────────────────────────────────

@courses_bp.route("/learning-path", methods=["GET"])
@jwt_required()
def get_learning_path():
    """
    Return the authenticated learner's active learning path.

    Returns:
        200: { learning_path }
        404: No learning path found
    """
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)
    if user is None:
        return error_response(404, "NOT_FOUND", "User not found.")

    path = (
        LearningPath.query
        .filter_by(user_id=user.id, goal_id=user.goal_id)
        .first()
    )
    if path is None:
        return error_response(404, "NOT_FOUND", "No learning path found. Complete the assessment first.")

    return success_response({"learning_path": _learning_path_schema.dump(path)})


@courses_bp.route("/learning-path/<path_id>", methods=["GET"])
@jwt_required()
def get_learning_path_by_id(path_id):
    """
    Return a specific learning path by ID (owner check enforced).

    Path param:
        path_id (str): UUID of the LearningPath

    Returns:
        200: { learning_path }
        403: Not your path
        404: Not found
    """
    user_id = get_jwt_identity()
    path = db.session.get(LearningPath, path_id)

    if path is None:
        return error_response(404, "NOT_FOUND", "Learning path not found.")
    if str(path.user_id) != user_id:
        return error_response(403, "FORBIDDEN", "You do not own this learning path.")

    return success_response({"learning_path": _learning_path_schema.dump(path)})
