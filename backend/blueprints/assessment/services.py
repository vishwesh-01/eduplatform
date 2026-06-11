"""
assessment/services.py — Adaptive quiz engine + learning path generation.

Key flows:
  1. start_session()   — create quiz session, return first question
  2. process_answer()  — record answer, adapt difficulty, end or continue
  3. _complete_session() — score, persist skill_level, generate learning path
  4. _generate_learning_path() — call LLM, seed courses into DB, enrol user
"""

import logging
from datetime import datetime, timezone, timedelta

from sqlalchemy import func

from ...extensions import db
from ...models import (
    Goal, LearningPath, LearningPathItem, Module, QuizAnswer,
    QuizQuestion, QuizSession, User, UserCourse, Course,
)
from ...models.quiz import QuizStatus, QuestionSource

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────
MIN_QUESTIONS           = 5
MAX_QUESTIONS           = 15
PLATEAU_WINDOW          = 3
START_DIFFICULTY        = 3
SESSION_TIMEOUT_MINUTES = 30
LLM_QUESTION_THRESHOLD  = 10

# Hardcoded fallback courses per goal (used when LLM fails)
FALLBACK_COURSES = {
    "Java Developer": [
        {"title": "Java Fundamentals", "description": "Core Java syntax, OOP principles, and standard library.", "estimated_hours": 20, "skill_level_required": 0, "estimated_skill_gain": 20},
        {"title": "Data Structures in Java", "description": "Arrays, lists, maps, trees, and algorithm complexity.", "estimated_hours": 15, "skill_level_required": 20, "estimated_skill_gain": 15},
        {"title": "Java Web Development with Spring Boot", "description": "Build REST APIs with Spring Boot, JPA, and security.", "estimated_hours": 25, "skill_level_required": 35, "estimated_skill_gain": 20},
        {"title": "Microservices with Java", "description": "Microservice patterns, Docker, Kubernetes basics.", "estimated_hours": 20, "skill_level_required": 55, "estimated_skill_gain": 15},
        {"title": "Java Testing & CI/CD", "description": "JUnit 5, Mockito, GitHub Actions, deployment.", "estimated_hours": 15, "skill_level_required": 70, "estimated_skill_gain": 10},
    ],
    "Python Developer": [
        {"title": "Python Fundamentals", "description": "Syntax, data types, functions, file I/O.", "estimated_hours": 18, "skill_level_required": 0, "estimated_skill_gain": 20},
        {"title": "Python OOP & Design Patterns", "description": "Classes, inheritance, decorators, design patterns.", "estimated_hours": 14, "skill_level_required": 20, "estimated_skill_gain": 15},
        {"title": "Web Development with Django", "description": "Build full-stack web apps with Django and PostgreSQL.", "estimated_hours": 22, "skill_level_required": 35, "estimated_skill_gain": 20},
        {"title": "Python for Data Engineering", "description": "Pandas, NumPy, SQLAlchemy, data pipelines.", "estimated_hours": 18, "skill_level_required": 55, "estimated_skill_gain": 15},
        {"title": "FastAPI & Async Python", "description": "High-performance APIs with FastAPI, async/await.", "estimated_hours": 14, "skill_level_required": 65, "estimated_skill_gain": 12},
    ],
    "Web Developer": [
        {"title": "HTML5 & CSS3 Fundamentals", "description": "Semantic HTML, Flexbox, Grid, responsive design.", "estimated_hours": 15, "skill_level_required": 0, "estimated_skill_gain": 18},
        {"title": "JavaScript Essentials", "description": "ES6+, DOM manipulation, async/await, Fetch API.", "estimated_hours": 20, "skill_level_required": 18, "estimated_skill_gain": 20},
        {"title": "React.js Complete Guide", "description": "Components, hooks, state management, React Router.", "estimated_hours": 25, "skill_level_required": 38, "estimated_skill_gain": 20},
        {"title": "Node.js & Express APIs", "description": "Build RESTful APIs, middleware, authentication.", "estimated_hours": 18, "skill_level_required": 55, "estimated_skill_gain": 15},
        {"title": "Full Stack Deployment", "description": "Docker, Nginx, cloud deployment, CI/CD pipelines.", "estimated_hours": 12, "skill_level_required": 70, "estimated_skill_gain": 10},
    ],
    "Data Scientist": [
        {"title": "Python for Data Science", "description": "NumPy, Pandas, data cleaning, EDA.", "estimated_hours": 18, "skill_level_required": 0, "estimated_skill_gain": 20},
        {"title": "Data Visualisation", "description": "Matplotlib, Seaborn, Plotly dashboards.", "estimated_hours": 12, "skill_level_required": 20, "estimated_skill_gain": 12},
        {"title": "Machine Learning Fundamentals", "description": "Supervised & unsupervised learning with scikit-learn.", "estimated_hours": 25, "skill_level_required": 32, "estimated_skill_gain": 20},
        {"title": "Deep Learning with PyTorch", "description": "Neural networks, CNNs, transfer learning.", "estimated_hours": 28, "skill_level_required": 52, "estimated_skill_gain": 20},
        {"title": "MLOps & Model Deployment", "description": "MLflow, Docker, REST APIs for ML models.", "estimated_hours": 15, "skill_level_required": 72, "estimated_skill_gain": 10},
    ],
    "Mobile App Developer": [
        {"title": "Flutter Fundamentals", "description": "Dart language, widgets, state management basics.", "estimated_hours": 20, "skill_level_required": 0, "estimated_skill_gain": 20},
        {"title": "Flutter UI & Animations", "description": "Custom widgets, animations, responsive layouts.", "estimated_hours": 15, "skill_level_required": 20, "estimated_skill_gain": 15},
        {"title": "State Management with Riverpod", "description": "Riverpod, Provider, clean architecture.", "estimated_hours": 18, "skill_level_required": 35, "estimated_skill_gain": 18},
        {"title": "Firebase & Backend Integration", "description": "Auth, Firestore, push notifications.", "estimated_hours": 15, "skill_level_required": 53, "estimated_skill_gain": 15},
        {"title": "App Store Deployment", "description": "Google Play, App Store, CI/CD with Fastlane.", "estimated_hours": 10, "skill_level_required": 68, "estimated_skill_gain": 10},
    ],
    "DevOps Engineer": [
        {"title": "Linux & Shell Scripting", "description": "Bash, file system, process management, cron.", "estimated_hours": 15, "skill_level_required": 0, "estimated_skill_gain": 18},
        {"title": "Docker & Containers", "description": "Containerisation, Dockerfiles, Docker Compose.", "estimated_hours": 18, "skill_level_required": 18, "estimated_skill_gain": 18},
        {"title": "Kubernetes Fundamentals", "description": "Pods, deployments, services, Helm charts.", "estimated_hours": 22, "skill_level_required": 36, "estimated_skill_gain": 20},
        {"title": "CI/CD with GitHub Actions", "description": "Pipelines, automated testing, deployment workflows.", "estimated_hours": 15, "skill_level_required": 56, "estimated_skill_gain": 15},
        {"title": "Cloud Infrastructure with Terraform", "description": "AWS/GCP IaC, modules, state management.", "estimated_hours": 20, "skill_level_required": 71, "estimated_skill_gain": 12},
    ],
}

# Default modules per course title (used to seed modules when a course is created)
DEFAULT_MODULES = {
    "Java Fundamentals":                    ["Introduction & Setup", "Variables & Data Types", "Control Flow", "Methods & Functions", "Object-Oriented Programming", "Exception Handling", "Collections Framework", "File I/O"],
    "Data Structures in Java":              ["Arrays & Strings", "Linked Lists", "Stacks & Queues", "Trees & Graphs", "Hash Maps", "Sorting Algorithms", "Searching Algorithms", "Big-O Analysis"],
    "Java Web Development with Spring Boot":["Spring Boot Basics", "REST API Design", "Spring Data JPA", "Authentication & JWT", "Testing with JUnit", "Deployment"],
    "Microservices with Java":              ["Microservice Architecture", "Service Discovery", "API Gateway", "Docker Basics", "Kubernetes Intro", "Monitoring"],
    "Java Testing & CI/CD":                 ["Unit Testing JUnit 5", "Mocking with Mockito", "Integration Testing", "GitHub Actions", "Docker CI", "Production Deploy"],
    "Python Fundamentals":                  ["Python Setup & Syntax", "Data Types & Structures", "Control Flow", "Functions & Modules", "File Handling", "Error Handling", "Standard Library", "Virtual Environments"],
    "Python OOP & Design Patterns":         ["Classes & Objects", "Inheritance & Polymorphism", "Magic Methods", "Decorators", "Design Patterns", "Type Hints"],
    "Web Development with Django":          ["Django Setup & MTV", "Models & ORM", "Views & Templates", "Forms & Validation", "Authentication", "REST API with DRF", "Deployment"],
    "Python for Data Engineering":          ["Pandas Fundamentals", "NumPy Essentials", "Data Cleaning", "SQLAlchemy", "Data Pipelines", "ETL Patterns"],
    "FastAPI & Async Python":               ["Async/Await Basics", "FastAPI Routing", "Pydantic Models", "Database Integration", "Auth & Security", "Deployment"],
    "HTML5 & CSS3 Fundamentals":            ["HTML Semantic Structure", "CSS Selectors & Specificity", "Flexbox Layout", "CSS Grid", "Responsive Design", "CSS Variables", "Animations"],
    "JavaScript Essentials":                ["Variables & Scope", "Functions & Closures", "Arrays & Objects", "DOM Manipulation", "Events", "Async & Promises", "Fetch API", "ES6+ Features"],
    "React.js Complete Guide":              ["React Fundamentals", "JSX & Components", "useState & useEffect", "Props & Context", "React Router", "Forms", "API Integration", "Performance Optimisation"],
    "Node.js & Express APIs":               ["Node.js Basics", "Express Setup", "Routing & Middleware", "Database with Sequelize", "Authentication", "File Uploads", "Testing APIs"],
    "Full Stack Deployment":                ["Docker for Web Apps", "Nginx Configuration", "SSL & HTTPS", "Cloud Provider Setup", "CI/CD Pipeline", "Monitoring & Logging"],
    "Python for Data Science":              ["NumPy Arrays", "Pandas DataFrames", "Data Cleaning", "Exploratory Analysis", "Statistical Analysis", "Feature Engineering"],
    "Data Visualisation":                   ["Matplotlib Basics", "Seaborn Charts", "Plotly Interactive", "Dashboard Design", "Storytelling with Data"],
    "Machine Learning Fundamentals":        ["ML Concepts", "Linear Regression", "Classification", "Decision Trees", "Model Evaluation", "Cross-Validation", "Feature Selection", "scikit-learn"],
    "Deep Learning with PyTorch":           ["Neural Network Basics", "PyTorch Tensors", "CNNs", "RNNs & LSTMs", "Transfer Learning", "Model Deployment"],
    "MLOps & Model Deployment":             ["MLflow Tracking", "Model Registry", "REST API for ML", "Docker for ML", "Monitoring Models"],
    "Flutter Fundamentals":                 ["Dart Language", "Flutter Widgets", "Layouts & Theming", "Navigation", "State Management Basics"],
    "Flutter UI & Animations":              ["Custom Widgets", "Implicit Animations", "Explicit Animations", "Responsive Layouts", "Theming"],
    "State Management with Riverpod":       ["Riverpod Basics", "Providers", "AsyncNotifier", "Clean Architecture", "Testing"],
    "Firebase & Backend Integration":       ["Firebase Auth", "Firestore CRUD", "Real-time Updates", "Push Notifications", "Analytics"],
    "App Store Deployment":                 ["Android Release Build", "iOS Provisioning", "Google Play Store", "App Store Connect", "CI/CD Fastlane"],
    "Linux & Shell Scripting":              ["Linux File System", "Bash Scripting", "Processes & Services", "Networking Basics", "Cron Jobs"],
    "Docker & Containers":                  ["Container Concepts", "Dockerfile", "Docker Compose", "Volumes & Networks", "Registry & Hub"],
    "Kubernetes Fundamentals":              ["K8s Architecture", "Pods & Deployments", "Services & Ingress", "ConfigMaps & Secrets", "Helm Charts", "Scaling"],
    "CI/CD with GitHub Actions":            ["Actions Basics", "Workflows & Triggers", "Testing Jobs", "Docker Build & Push", "Deploy to Cloud"],
    "Cloud Infrastructure with Terraform":  ["IaC Concepts", "Terraform Basics", "AWS Resources", "Modules", "State Management", "CI/CD with Terraform"],
}


def start_session(user_id: str) -> tuple:
    """Create a new quiz session and return the first question."""
    user = db.session.get(User, user_id)
    if user is None or user.goal_id is None:
        raise ValueError("NO_GOAL")

    question_count = QuizQuestion.query.filter_by(goal_id=user.goal_id).count()
    if question_count < MIN_QUESTIONS:
        raise ValueError("INSUFFICIENT_QUESTIONS")

    _abandon_stale_sessions(user_id)

    session = QuizSession(
        user_id=user.id,
        goal_id=user.goal_id,
        current_difficulty=START_DIFFICULTY,
        status=QuizStatus.in_progress,
    )
    db.session.add(session)
    db.session.flush()

    first_question = _select_question(session, set())
    if first_question is None:
        raise ValueError("INSUFFICIENT_QUESTIONS")

    db.session.commit()
    return session, first_question


def process_answer(session_id: str, question_id: str, selected_option: int, user_id: str) -> dict:
    """Record an answer, adjust difficulty, and return next question or completion."""
    session = db.session.get(QuizSession, session_id)
    if session is None or str(session.user_id) != user_id:
        raise ValueError("SESSION_NOT_FOUND")
    if session.status != QuizStatus.in_progress:
        raise ValueError("SESSION_NOT_ACTIVE")

    question = db.session.get(QuizQuestion, question_id)
    if question is None:
        raise ValueError("QUESTION_NOT_FOUND")

    is_correct = (selected_option == question.correct_option_index)
    answer = QuizAnswer(
        session_id=session.id,
        question_id=question.id,
        selected_option=selected_option,
        is_correct=is_correct,
    )
    db.session.add(answer)

    # Adapt difficulty
    if is_correct:
        session.current_difficulty = min(session.current_difficulty + 1, 5)
    else:
        session.current_difficulty = max(session.current_difficulty - 1, 1)

    session.current_question_number += 1
    session.total_questions = session.current_question_number

    all_answers = (
        QuizAnswer.query
        .filter_by(session_id=session.id)
        .order_by(QuizAnswer.answered_at)
        .all()
    )

    if _should_end(session, all_answers):
        return _complete_session(session, all_answers)

    answered_ids = {str(a.question_id) for a in all_answers}
    _maybe_generate_questions(session, answered_ids)

    next_q = _select_question(session, answered_ids)
    if next_q is None:
        return _complete_session(session, all_answers)

    db.session.commit()
    return {"status": "continue", "next_question": next_q, "session": session}


def get_session(session_id: str, user_id: str) -> QuizSession:
    """Retrieve a session for display/resume (ownership check)."""
    session = db.session.get(QuizSession, session_id)
    if session is None or str(session.user_id) != user_id:
        raise ValueError("SESSION_NOT_FOUND")
    return session


# ── Private helpers ───────────────────────────────────────────────────────────

def _select_question(session: QuizSession, answered_ids: set):
    """Select next question at current difficulty, with fallback to adjacent levels."""
    for offset in [0, 1, -1, 2, -2, 3, -3]:
        difficulty = session.current_difficulty + offset
        if difficulty < 1 or difficulty > 5:
            continue
        query = QuizQuestion.query.filter(
            QuizQuestion.goal_id == session.goal_id,
            QuizQuestion.difficulty == difficulty,
        )
        if answered_ids:
            query = query.filter(QuizQuestion.id.notin_(answered_ids))
        question = query.order_by(func.random()).first()
        if question:
            return question
    return None


def _should_end(session: QuizSession, answers: list) -> bool:
    """Return True when the session should end."""
    n = len(answers)
    if n >= MAX_QUESTIONS:
        return True
    if n >= MIN_QUESTIONS and len(answers) >= PLATEAU_WINDOW:
        recent = answers[-PLATEAU_WINDOW:]
        if len({a.question.difficulty for a in recent}) == 1:
            return True
    return False


def _complete_session(session: QuizSession, answers: list) -> dict:
    """Finalise session: compute skill, save to user, trigger path generation."""
    skill_level = _calculate_skill_level(answers)
    session.score        = skill_level
    session.status       = QuizStatus.completed
    session.completed_at = datetime.now(timezone.utc)

    user = db.session.get(User, str(session.user_id))
    if user:
        user.skill_level = int(skill_level)

    db.session.commit()

    try:
        _generate_learning_path(user, session)
    except Exception as exc:
        logger.error(f"Learning path generation failed: {exc}")

    return {"status": "completed", "session": session, "skill_level": skill_level}


def _calculate_skill_level(answers: list) -> float:
    """Weighted score: 60% accuracy + 40% difficulty normalised to 0-100."""
    if not answers:
        return 0.0
    correct  = sum(1 for a in answers if a.is_correct)
    total    = len(answers)
    avg_diff = sum(a.question.difficulty for a in answers) / total
    raw_acc  = correct / total
    diff_norm = (avg_diff - 1) / 4
    score = (raw_acc * 0.6 + diff_norm * 0.4) * 100
    return round(max(0.0, min(100.0, score)), 2)


def _abandon_stale_sessions(user_id: str) -> None:
    """Mark in-progress sessions older than SESSION_TIMEOUT_MINUTES as abandoned."""
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=SESSION_TIMEOUT_MINUTES)
    stale = QuizSession.query.filter(
        QuizSession.user_id == user_id,
        QuizSession.status  == QuizStatus.in_progress,
        QuizSession.started_at < cutoff,
    ).all()
    for s in stale:
        s.status = QuizStatus.abandoned
    if stale:
        db.session.commit()


def _maybe_generate_questions(session: QuizSession, answered_ids: set) -> None:
    """Generate LLM questions if the bank is running low."""
    try:
        remaining = QuizQuestion.query.filter(
            QuizQuestion.goal_id == session.goal_id,
        ).count() - len(answered_ids)
        if remaining >= LLM_QUESTION_THRESHOLD:
            return
        from ..ai.llm_service import LLMService
        goal = db.session.get(Goal, str(session.goal_id))
        if goal is None:
            return
        llm    = LLMService()
        result = llm.generate_quiz_questions(goal=goal.name, difficulty=session.current_difficulty, count=5)
        if result:
            for item in result.questions:
                q = QuizQuestion(
                    goal_id=session.goal_id,
                    question_text=item.question_text,
                    options=item.options,
                    correct_option_index=item.correct_option_index,
                    difficulty=item.difficulty,
                    source=QuestionSource.ai,
                )
                db.session.add(q)
            db.session.commit()
            logger.info(f"Generated {len(result.questions)} AI questions for {goal.name}")
    except Exception as exc:
        logger.warning(f"LLM question generation skipped: {exc}")


def _get_or_create_course(goal_id, title: str, course_data: dict) -> Course:
    """
    Get a course by goal+title, or create it with default modules.
    This ensures every LLM-recommended course exists in the DB with real modules.
    """
    course = Course.query.filter_by(goal_id=goal_id, title=title).first()
    if course:
        return course

    course = Course(
        goal_id=goal_id,
        title=title,
        instructor="AI Curated",
        duration_hours=course_data.get("estimated_hours", 10),
    )
    db.session.add(course)
    db.session.flush()

    # Add default modules for this course title
    module_titles = DEFAULT_MODULES.get(title, [
        "Introduction & Overview",
        "Core Concepts",
        "Practical Application",
        "Advanced Topics",
        "Project & Review",
    ])
    for pos, mod_title in enumerate(module_titles, start=1):
        db.session.add(Module(
            course_id=course.id,
            title=mod_title,
            position=pos,
        ))
    db.session.flush()
    return course


def _generate_learning_path(user: User, session: QuizSession) -> None:
    """
    Build personalised learning path after assessment completes.

    Steps:
    1. Try LLM for recommendations
    2. Fall back to hardcoded courses per goal if LLM fails
    3. Ensure every recommended course exists in DB with modules
    4. Auto-enrol user in all path courses
    5. Persist learning_paths + learning_path_items rows
    """
    goal = db.session.get(Goal, str(session.goal_id))
    if goal is None:
        return

    completed_titles = [
        uc.course.title
        for uc in user.user_courses
        if uc.completed_at is not None and uc.course
    ]

    # 1. Try LLM
    from ..ai.llm_service import LLMService
    llm    = LLMService()
    result = llm.generate_learning_path(
        user_id=str(user.id),
        goal=goal.name,
        skill_level=int(user.skill_level or 0),
        completed_courses=completed_titles,
    )

    if result and result.courses:
        course_data_list = [c.model_dump() for c in result.courses]
        logger.info(f"LLM generated {len(course_data_list)} courses for {user.id}")
    else:
        # 2. Fallback: use hardcoded courses filtered by skill level
        skill = int(user.skill_level or 0)
        all_fallbacks = FALLBACK_COURSES.get(goal.name, list(FALLBACK_COURSES.values())[0])
        # Filter to appropriate skill range and exclude completed
        course_data_list = [
            c for c in all_fallbacks
            if c["title"] not in completed_titles
            and c["skill_level_required"] <= max(skill + 20, 30)
        ][:5]
        if not course_data_list:
            course_data_list = all_fallbacks[:5]
        logger.info(f"Using {len(course_data_list)} fallback courses for {user.id}")

    # 3. Delete existing path for this user+goal
    existing = LearningPath.query.filter_by(user_id=user.id, goal_id=goal.id).first()
    if existing:
        db.session.delete(existing)
        db.session.flush()

    path = LearningPath(user_id=user.id, goal_id=goal.id)
    db.session.add(path)
    db.session.flush()

    # 4. Ensure each course exists in DB; auto-enrol user; create path items
    for position, cdata in enumerate(course_data_list, start=1):
        course = _get_or_create_course(goal.id, cdata["title"], cdata)

        # Auto-enrol user in this course so it appears on dashboard
        enrolment = db.session.get(UserCourse, (str(user.id), str(course.id)))
        if enrolment is None:
            enrolment = UserCourse(user_id=user.id, course_id=course.id)
            db.session.add(enrolment)

        path_item = LearningPathItem(
            path_id=path.id,
            course_id=course.id,
            position=position,
            estimated_skill_gain=cdata.get("estimated_skill_gain", 10),
        )
        db.session.add(path_item)

    db.session.commit()
    logger.info(f"Learning path created for user {user.id} with {len(course_data_list)} courses")


def adaptive_update_after_module(user_id: str, module_id: str) -> None:
    """
    Called after a learner completes a module.
    Re-generates the REMAINING learning path using the LLM based on updated progress.
    This is the per-module adaptive update feature.

    Args:
        user_id:   UUID of the learner.
        module_id: UUID of the module just completed.
    """
    user = db.session.get(User, user_id)
    if user is None or user.goal_id is None:
        return

    goal = db.session.get(Goal, str(user.goal_id))
    if goal is None:
        return

    # Get current learning path
    path = LearningPath.query.filter_by(user_id=user.id, goal_id=goal.id).first()
    if path is None:
        return

    # Module just completed
    module = db.session.get(Module, module_id)
    module_title = module.title if module else "Unknown Module"

    # Fully completed courses
    completed_courses = [
        uc.course.title
        for uc in user.user_courses
        if uc.completed_at is not None and uc.course
    ]

    # Remaining courses in path (not yet completed)
    remaining_titles = [
        item.course.title
        for item in path.items
        if item.course and item.course.title not in completed_courses
    ]

    # Only call LLM if there are remaining items to adapt
    if not remaining_titles:
        return

    from ..ai.llm_service import LLMService
    llm = LLMService()
    result = llm.generate_adaptive_path_update(
        user_id=user_id,
        goal=goal.name,
        current_skill=int(user.skill_level or 0),
        completed_courses=completed_courses,
        remaining_path_titles=remaining_titles,
        module_just_completed=module_title,
    )

    if result is None or not result.courses:
        logger.info(f"Adaptive update skipped (LLM unavailable) for user {user_id}")
        return

    # Remove current remaining path items
    for item in list(path.items):
        if item.course and item.course.title not in completed_courses:
            db.session.delete(item)
    db.session.flush()

    # Determine current max position (from completed items) to continue numbering
    completed_items = [
        item for item in path.items
        if item.course and item.course.title in completed_courses
    ]
    start_position = max((i.position for i in completed_items), default=0) + 1

    # Insert the new adapted courses
    for i, cdata in enumerate(result.courses):
        course = _get_or_create_course(goal.id, cdata.title, cdata.model_dump())

        # Enrol user if not already
        enrolment = db.session.get(UserCourse, (user_id, str(course.id)))
        if enrolment is None:
            enrolment = UserCourse(user_id=user_id, course_id=course.id)
            db.session.add(enrolment)

        path_item = LearningPathItem(
            path_id=path.id,
            course_id=course.id,
            position=start_position + i,
            estimated_skill_gain=cdata.estimated_skill_gain,
        )
        db.session.add(path_item)

    path.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    logger.info(f"Adaptive path updated for user {user_id} after module '{module_title}': {len(result.courses)} new items")
