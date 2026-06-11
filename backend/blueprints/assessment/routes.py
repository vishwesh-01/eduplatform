"""
assessment/routes.py — HTTP routes for the adaptive assessment engine.

Endpoints:
    POST /api/v1/assessment/start            — Start a new quiz session
    POST /api/v1/assessment/answer           — Submit an answer
    GET  /api/v1/assessment/session/<id>     — Resume/inspect a session
"""

import logging

from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from marshmallow import ValidationError

from ...app import error_response, success_response
from . import assessment_bp
from .schemas import QuestionSchema, SessionSchema, SubmitAnswerSchema
from .services import get_session, process_answer, start_session

logger = logging.getLogger(__name__)

_session_schema  = SessionSchema()
_question_schema = QuestionSchema()
_answer_schema   = SubmitAnswerSchema()


@assessment_bp.route("/start", methods=["POST"])
@jwt_required()
def start():
    """
    Create a new adaptive quiz session and return the first question.

    Returns:
        201: { session, question }
        400: No learning goal set
        503: Insufficient questions in the bank
    """
    user_id = get_jwt_identity()
    try:
        session, question = start_session(user_id)
    except ValueError as e:
        code = str(e)
        if code == "NO_GOAL":
            return error_response(400, "NO_GOAL", "Please select a learning goal before starting the assessment.")
        if code == "INSUFFICIENT_QUESTIONS":
            return error_response(
                503,
                "INSUFFICIENT_QUESTIONS",
                "Not enough questions available for this goal. Please try again later.",
            )
        return error_response(400, "BAD_REQUEST", str(e))

    return success_response(
        {
            "session":  _session_schema.dump(session),
            "question": _question_schema.dump(question),
        },
        status=201,
    )


@assessment_bp.route("/answer", methods=["POST"])
@jwt_required()
def answer():
    """
    Submit an answer for the current question in a quiz session.

    Request body:
        session_id      (str): UUID of the active session
        question_id     (str): UUID of the question being answered
        selected_option (int): 0-3 index of the chosen option

    Returns:
        200: { status: 'continue', next_question, session }
         OR { status: 'completed', session, skill_level }
        400: Invalid session or answer
        422: Validation error
    """
    user_id = get_jwt_identity()

    try:
        data = _answer_schema.load(request.get_json() or {})
    except ValidationError as err:
        details = [{"field": f, "message": m[0]} for f, m in err.messages.items()]
        return error_response(422, "VALIDATION_ERROR", "Invalid answer payload.", details)

    try:
        result = process_answer(
            session_id=data["session_id"],
            question_id=data["question_id"],
            selected_option=data["selected_option"],
            user_id=user_id,
        )
    except ValueError as e:
        return error_response(400, "BAD_REQUEST", str(e))

    response_data = {
        "status":  result["status"],
        "session": _session_schema.dump(result["session"]),
    }

    if result["status"] == "continue":
        response_data["next_question"] = _question_schema.dump(result["next_question"])
    else:
        response_data["skill_level"] = result.get("skill_level")

    return success_response(response_data)


@assessment_bp.route("/session/<session_id>", methods=["GET"])
@jwt_required()
def get_session_route(session_id):
    """
    Return the current state of a quiz session (used to resume after reconnect).

    Path param:
        session_id (str): UUID of the quiz session

    Returns:
        200: { session }
        403: Session does not belong to caller
        404: Session not found
    """
    user_id = get_jwt_identity()
    try:
        session = get_session(session_id, user_id)
    except ValueError:
        return error_response(404, "NOT_FOUND", "Session not found or access denied.")

    return success_response({"session": _session_schema.dump(session)})
