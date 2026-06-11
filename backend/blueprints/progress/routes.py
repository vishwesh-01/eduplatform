"""
progress/routes.py — Progress tracking endpoints.

Endpoints:
    POST /api/v1/progress/module/<module_id>/complete — Mark module done
    GET  /api/v1/progress/course/<course_id>          — Per-course progress
    GET  /api/v1/progress/summary                     — Overall dashboard summary
"""

from flask_jwt_extended import get_jwt_identity, jwt_required

from ...app import error_response, success_response
from . import progress_bp
from .services import complete_module, get_course_progress, get_progress_summary


@progress_bp.route("/module/<module_id>/complete", methods=["POST"])
@jwt_required()
def mark_module_complete(module_id):
    """
    Mark a module as complete for the authenticated learner.

    Path param:
        module_id (str): UUID of the Module

    Returns:
        200: { module_id, course_id, completion_percentage, certificate_code }
        404: Module not found
    """
    user_id = get_jwt_identity()
    try:
        result = complete_module(user_id, module_id)
    except ValueError as e:
        return error_response(404, "NOT_FOUND", str(e))

    return success_response(result)


@progress_bp.route("/course/<course_id>", methods=["GET"])
@jwt_required()
def course_progress(course_id):
    """
    Return completion percentage and completed module IDs for a course.

    Path param:
        course_id (str): UUID of the Course

    Returns:
        200: { course_id, completion_percentage, completed_module_ids }
    """
    user_id = get_jwt_identity()
    result = get_course_progress(user_id, course_id)
    return success_response(result)


@progress_bp.route("/summary", methods=["GET"])
@jwt_required()
def progress_summary():
    """
    Return an overall progress summary for the learner's dashboard.

    Returns:
        200: { overall_completion_pct, streak_days, quiz_history, course_statuses,
               total_enrolled, certificates_earned, skill_level }
    """
    user_id = get_jwt_identity()
    result = get_progress_summary(user_id)
    return success_response(result)
