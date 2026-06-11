"""
progress/services.py — ProgressService: module completion and streak tracking.
"""

import logging
from datetime import datetime, timezone, timedelta
from decimal import Decimal

from sqlalchemy import func

from ...extensions import db
from ...models import Certificate, Course, Module, UserCourse, UserModuleProgress, User

logger = logging.getLogger(__name__)


def complete_module(user_id: str, module_id: str) -> dict:
    """
    Mark a module as complete for a learner. Recalculates course completion
    percentage and auto-issues a certificate when a course reaches 100%.

    Args:
        user_id:   UUID string of the learner.
        module_id: UUID string of the Module being completed.

    Returns:
        Dict with completion_percentage and certificate_code (if issued).

    Raises:
        ValueError: If module or user not found.
    """
    module = db.session.get(Module, module_id)
    if module is None:
        raise ValueError("MODULE_NOT_FOUND")

    user = db.session.get(User, user_id)
    if user is None:
        raise ValueError("USER_NOT_FOUND")

    # Upsert: insert progress record if not already present (idempotent)
    existing = db.session.get(UserModuleProgress, (user_id, module_id))
    if existing is None:
        progress = UserModuleProgress(user_id=user_id, module_id=module_id)
        db.session.add(progress)
        db.session.flush()

    # Ensure the user is enrolled in the course
    course_id = str(module.course_id)
    user_course = db.session.get(UserCourse, (user_id, course_id))
    if user_course is None:
        user_course = UserCourse(user_id=user_id, course_id=course_id)
        db.session.add(user_course)
        db.session.flush()

    # Recalculate completion percentage
    total_modules = Module.query.filter_by(course_id=course_id).count()
    completed_modules = (
        db.session.query(func.count(UserModuleProgress.module_id))
        .join(Module, Module.id == UserModuleProgress.module_id)
        .filter(
            UserModuleProgress.user_id == user_id,
            Module.course_id == course_id,
        )
        .scalar()
    )

    pct = round((completed_modules / total_modules) * 100, 2) if total_modules else 0

    # Round to nearest whole number for display; use Decimal for DB precision
    user_course.completion_percentage = Decimal(str(pct))

    certificate_code = None

    # Auto-issue certificate when course is fully complete
    if pct >= 100.0 and user_course.completed_at is None:
        user_course.completed_at = datetime.now(timezone.utc)

        # Idempotent certificate issuance
        existing_cert = Certificate.query.filter_by(
            user_id=user_id, course_id=course_id
        ).first()
        if existing_cert is None:
            from ...models import certificate as cert_model
            cert = Certificate(user_id=user_id, course_id=course_id)
            db.session.add(cert)
            db.session.flush()
            certificate_code = str(cert.certificate_code)

        # Re-evaluate learning path now that a course is complete
        try:
            _re_evaluate_path(user)
        except Exception as exc:
            logger.warning(f"Learning path re-evaluation failed: {exc}")

    db.session.commit()

    # Update user last_active_at
    user.last_active_at = datetime.now(timezone.utc)
    db.session.commit()

    return {
        "module_id":            module_id,
        "course_id":            course_id,
        "completion_percentage": float(pct),
        "certificate_code":      certificate_code,
    }


def get_course_progress(user_id: str, course_id: str) -> dict:
    """
    Return completion percentage and list of completed module IDs for a course.

    Args:
        user_id:   UUID string of the learner.
        course_id: UUID string of the Course.

    Returns:
        Dict with completion_percentage and completed_module_ids.
    """
    user_course = db.session.get(UserCourse, (user_id, course_id))
    pct = float(user_course.completion_percentage) if user_course else 0.0

    completed_ids = [
        str(p.module_id)
        for p in UserModuleProgress.query
        .join(Module, Module.id == UserModuleProgress.module_id)
        .filter(
            UserModuleProgress.user_id == user_id,
            Module.course_id == course_id,
        )
        .all()
    ]

    return {
        "course_id":            course_id,
        "completion_percentage": pct,
        "completed_module_ids":  completed_ids,
    }


def get_progress_summary(user_id: str) -> dict:
    """
    Return an overall progress summary for the dashboard.

    Includes:
      - overall_completion_pct: average across all enrolled courses
      - streak_days: consecutive UTC calendar days with at least one module completion
      - quiz_history: list of { date, score } for the quiz score line chart
      - course_statuses: list of { course_id, title, completion_percentage }

    Args:
        user_id: UUID string of the learner.

    Returns:
        Dict with summary data.
    """
    user = db.session.get(User, user_id)
    if user is None:
        return {}

    enrolled = UserCourse.query.filter_by(user_id=user_id).all()
    total_enrolled = len(enrolled)

    if total_enrolled == 0:
        overall_pct = 0.0
    else:
        overall_pct = round(
            sum(float(uc.completion_percentage) for uc in enrolled) / total_enrolled, 2
        )

    # Course statuses for doughnut chart and progress list
    course_statuses = []
    for uc in enrolled:
        course = db.session.get(Course, str(uc.course_id))
        if course:
            course_statuses.append({
                "course_id":            str(uc.course_id),
                "title":                course.title,
                "completion_percentage": float(uc.completion_percentage),
                "completed":            uc.completed_at is not None,
            })

    # Quiz history for line chart
    from ...models import QuizSession
    from ...models.quiz import QuizStatus
    sessions = (
        QuizSession.query
        .filter_by(user_id=user_id, status=QuizStatus.completed)
        .order_by(QuizSession.completed_at)
        .all()
    )
    quiz_history = [
        {
            "date":  s.completed_at.strftime("%Y-%m-%d") if s.completed_at else "",
            "score": float(s.score) if s.score is not None else 0,
        }
        for s in sessions
    ]

    # Count certificates earned
    cert_count = Certificate.query.filter_by(user_id=user_id).count()

    return {
        "overall_completion_pct": overall_pct,
        "streak_days":            _calculate_streak(user_id),
        "quiz_history":           quiz_history,
        "course_statuses":        course_statuses,
        "total_enrolled":         total_enrolled,
        "certificates_earned":    cert_count,
        "skill_level":            user.skill_level,
    }


def _calculate_streak(user_id: str) -> int:
    """
    Count the number of consecutive UTC calendar days (ending today) on which
    the learner completed at least one module.

    Returns:
        Integer streak count (0 if no completions today or yesterday).
    """
    today = datetime.now(timezone.utc).date()
    streak = 0
    check_day = today

    while True:
        day_start = datetime(check_day.year, check_day.month, check_day.day, tzinfo=timezone.utc)
        day_end   = day_start + timedelta(days=1)

        count = (
            UserModuleProgress.query
            .filter(
                UserModuleProgress.user_id == user_id,
                UserModuleProgress.completed_at >= day_start,
                UserModuleProgress.completed_at < day_end,
            )
            .count()
        )

        if count == 0:
            break

        streak   += 1
        check_day = check_day - timedelta(days=1)

    return streak


def _re_evaluate_path(user: User) -> None:
    """
    After a course completion, re-check the learning path and optionally
    remove the newly completed course from the remaining path items.
    """
    from ...models import LearningPath, LearningPathItem

    if user.goal_id is None:
        return

    path = LearningPath.query.filter_by(user_id=user.id, goal_id=user.goal_id).first()
    if path is None:
        return

    completed_course_ids = {
        str(uc.course_id) for uc in user.user_courses if uc.completed_at is not None
    }

    for item in list(path.items):
        if str(item.course_id) in completed_course_ids:
            db.session.delete(item)

    db.session.commit()
