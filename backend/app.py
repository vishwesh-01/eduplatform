"""
app.py — Flask application factory.

Exposes a single `create_app(config_name=None)` function that:
  1. Validates all critical environment variables (exits on missing).
  2. Selects and loads the right Config class.
  3. Initialises all Flask extensions (db, jwt, cors, limiter, migrate).
  4. Registers all 8 feature blueprints under the /api/v1/ prefix.
  5. Attaches global HTTP error handlers.
  6. Attaches before/after request hooks for request-ID injection and
     structured JSON access logging.
  7. Registers JWT error callbacks that return envelope-formatted errors.

All JSON responses — success and error — use the standard envelope:
  {
    "data": <payload or null>,
    "error": <null or {"code": ..., "message": ..., "details": [...]}>,
    "meta": {"request_id": "...", "timestamp": "..."}
  }
"""

import logging
import time
from datetime import datetime, timezone
from uuid import uuid4

from flask import Flask, g, jsonify, request

from .config import config_map, validate_critical_env
from .extensions import cors, db, jwt, limiter, migrate

# ── Module-level logger ──────────────────────────────────────────────────────
logger = logging.getLogger(__name__)


# ── Response helpers ─────────────────────────────────────────────────────────

def _build_meta():
    """Return the meta block for the response envelope."""
    return {
        "request_id": getattr(g, "request_id", str(uuid4())),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def success_response(data, status=200):
    """
    Build a successful envelope response.

    Args:
        data:   Serialisable payload placed in "data".
        status: HTTP status code (default 200).

    Returns:
        Flask Response with Content-Type application/json.
    """
    return jsonify({"data": data, "error": None, "meta": _build_meta()}), status


def error_response(status, code, message, details=None):
    """
    Build an error envelope response.

    Args:
        status:   HTTP status code.
        code:     Machine-readable error code string (e.g. "NOT_FOUND").
        message:  Human-readable description.
        details:  Optional list of field-level error dicts (422 validation errors).

    Returns:
        Flask Response with Content-Type application/json.
    """
    error_body = {"code": code, "message": message}
    if details is not None:
        error_body["details"] = details
    return jsonify({"data": None, "error": error_body, "meta": _build_meta()}), status


# ── Application factory ──────────────────────────────────────────────────────

def create_app(config_name=None):
    """
    Flask application factory.

    Args:
        config_name: One of "development", "production", "testing".
                     Falls back to FLASK_ENV env var, then "development".

    Returns:
        Configured Flask application instance.
    """
    # ── 1. Validate critical environment variables before anything else ──────
    # This will call sys.exit(1) if any required var is missing, ensuring the
    # process manager (e.g. systemd, Docker) detects the failure immediately.
    validate_critical_env()

    # ── 2. Create the Flask app ──────────────────────────────────────────────
    app = Flask(__name__)

    # ── 3. Load configuration ────────────────────────────────────────────────
    import os
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    # Normalise: testing / production / anything else → development
    config_class = config_map.get(config_name, config_map["development"])
    app.config.from_object(config_class)

    # ── 4. Configure logging ─────────────────────────────────────────────────
    logging.basicConfig(
        level=app.config.get("LOG_LEVEL", logging.DEBUG),
        format='{"time":"%(asctime)s","level":"%(levelname)s","name":"%(name)s","message":"%(message)s"}',
        datefmt="%Y-%m-%dT%H:%M:%SZ",
    )

    # ── 5. Initialise extensions ─────────────────────────────────────────────
    _init_extensions(app)

    # ── 6. Register blueprints ───────────────────────────────────────────────
    _register_blueprints(app)

    # ── 7. Register error handlers ───────────────────────────────────────────
    _register_error_handlers(app)

    # ── 8. Register request lifecycle hooks ─────────────────────────────────
    _register_request_hooks(app)

    # ── 9. Register JWT error callbacks ─────────────────────────────────────
    _register_jwt_callbacks(app)

    logger.info(
        f"Flask app created in '{config_name}' mode "
        f"(debug={app.config['DEBUG']}, testing={app.config['TESTING']})"
    )
    return app


# ── Extension initialisation ─────────────────────────────────────────────────

def _init_extensions(app):
    """
    Bind all extension singletons to the Flask app.
    Extensions were instantiated without an app context in extensions.py;
    init_app() completes the binding.
    """
    from datetime import timedelta

    # SQLAlchemy — ORM and connection pool
    db.init_app(app)

    # Flask-Migrate — Alembic wrapper, point to backend/migrations/ directory
    import os
    migrations_dir = os.path.join(os.path.dirname(__file__), "migrations")
    migrate.init_app(app, db, directory=migrations_dir)

    # Flask-JWT-Extended — configure token lifetimes from Config values
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(
        minutes=app.config.get("JWT_ACCESS_TOKEN_EXPIRES_MINUTES", 15)
    )
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(
        days=app.config.get("JWT_REFRESH_TOKEN_EXPIRES_DAYS", 7)
    )
    jwt.init_app(app)

    # Flask-CORS — restrict origins to the allowlist in config
    cors.init_app(
        app,
        resources={r"/api/*": {"origins": app.config.get("ALLOWED_ORIGINS", [])}},
        supports_credentials=True,
    )

    # Flask-Limiter — rate limiting keyed by remote IP
    limiter.init_app(app)


# ── Blueprint registration ───────────────────────────────────────────────────

def _register_blueprints(app):
    """
    Import and register all 8 feature blueprints under /api/v1/.

    Each blueprint module is responsible for defining its own Blueprint
    object and URL prefix relative to /api/v1/. The ai blueprint has no
    HTTP routes (internal service only) but is imported here so its
    module-level setup runs inside the app context.
    """
    from .blueprints.admin import admin_bp
    from .blueprints.assessment import assessment_bp
    from .blueprints.auth import auth_bp
    from .blueprints.certificates import certificates_bp
    from .blueprints.courses import courses_bp
    from .blueprints.progress import progress_bp
    from .blueprints.youtube import youtube_bp
    # Note: ai blueprint has no HTTP routes; LLMService is used internally

    API_PREFIX = "/api/v1"

    app.register_blueprint(auth_bp, url_prefix=f"{API_PREFIX}/auth")
    app.register_blueprint(assessment_bp, url_prefix=f"{API_PREFIX}/assessment")
    app.register_blueprint(courses_bp, url_prefix=f"{API_PREFIX}")
    app.register_blueprint(progress_bp, url_prefix=f"{API_PREFIX}/progress")
    app.register_blueprint(certificates_bp, url_prefix=f"{API_PREFIX}/certificates")
    app.register_blueprint(admin_bp, url_prefix=f"{API_PREFIX}/admin")
    app.register_blueprint(youtube_bp, url_prefix=f"{API_PREFIX}/youtube")

    logger.debug("All blueprints registered under /api/v1/")


# ── Error handlers ───────────────────────────────────────────────────────────

def _register_error_handlers(app):
    """
    Register global HTTP error handlers that return envelope-formatted JSON.

    Handles: 404 Not Found, 405 Method Not Allowed, 413 Payload Too Large,
             422 Unprocessable Entity, 429 Too Many Requests, 500 Internal Error.
    """

    @app.errorhandler(404)
    def not_found(e):
        return error_response(404, "NOT_FOUND", "The requested resource was not found.")

    @app.errorhandler(405)
    def method_not_allowed(e):
        return error_response(405, "METHOD_NOT_ALLOWED", "HTTP method not allowed on this endpoint.")

    @app.errorhandler(413)
    def payload_too_large(e):
        # Flask raises this automatically when Content-Length > MAX_CONTENT_LENGTH
        return error_response(
            413,
            "PAYLOAD_TOO_LARGE",
            "Request body exceeds the 1 MB size limit.",
        )

    @app.errorhandler(422)
    def unprocessable_entity(e):
        # May carry field-level validation details from marshmallow/Werkzeug
        details = getattr(e, "data", {}).get("messages") if hasattr(e, "data") else None
        return error_response(
            422,
            "VALIDATION_ERROR",
            "Request body failed validation.",
            details=details,
        )

    @app.errorhandler(429)
    def rate_limited(e):
        return error_response(
            429,
            "RATE_LIMITED",
            "Too many requests. Please slow down and try again later.",
        )

    @app.errorhandler(500)
    def internal_server_error(e):
        # Log the exception with a traceback so it surfaces in application logs
        logger.exception("Unhandled server error: %s", e)
        return error_response(
            500,
            "INTERNAL_ERROR",
            "An unexpected error occurred. Please try again later.",
        )


# ── Request lifecycle hooks ──────────────────────────────────────────────────

def _register_request_hooks(app):
    """
    Register before_request and after_request hooks.

    before_request:
        - Assigns g.request_id  (UUID, used in every response envelope)
        - Records  g.start_time (monotonic float, used to compute response_time_ms)

    after_request:
        - Logs a structured JSON line per request:
          timestamp, method, path, status, response_time_ms, user_id, request_id
    """

    @app.before_request
    def set_request_context():
        """Inject a unique request ID and start timer into Flask's g context."""
        g.request_id = str(uuid4())
        g.start_time = time.monotonic()

    @app.after_request
    def log_request(response):
        """Emit a structured access-log entry after every request."""
        # Resolve elapsed time; guard against missing start_time (e.g. early abort)
        elapsed_ms = round((time.monotonic() - getattr(g, "start_time", time.monotonic())) * 1000, 2)

        # Attempt to extract the authenticated user ID from the JWT identity.
        # We import here to avoid circular imports at module load time.
        user_id = None
        try:
            from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
            verify_jwt_in_request(optional=True)
            user_id = get_jwt_identity()
        except Exception:
            # JWT absent or invalid — that is fine for public endpoints
            pass

        logger.info(
            "",
            extra={
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "method": request.method,
                "path": request.path,
                "status": response.status_code,
                "response_time_ms": elapsed_ms,
                "user_id": user_id,
                "request_id": getattr(g, "request_id", None),
            },
        )
        return response


# ── JWT error callbacks ──────────────────────────────────────────────────────

def _register_jwt_callbacks(app):
    """
    Register Flask-JWT-Extended error callbacks so JWT failures return
    envelope-formatted JSON responses rather than default HTML/plain text.
    """

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        """Access or refresh token has passed its exp claim."""
        return error_response(
            401,
            "TOKEN_EXPIRED",
            "Your token has expired. Please log in again.",
        )

    @jwt.invalid_token_loader
    def invalid_token_callback(error_string):
        """Token signature is invalid, malformed, or tampered."""
        return error_response(
            401,
            "UNAUTHORIZED",
            "Invalid token. Please log in again.",
        )

    @jwt.unauthorized_loader
    def missing_token_callback(error_string):
        """No JWT was provided in the Authorization header."""
        return error_response(
            401,
            "UNAUTHORIZED",
            "Authentication token is required.",
        )

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        """Token JTI is present in the token blocklist (logged out)."""
        return error_response(
            401,
            "TOKEN_REVOKED",
            "This token has been revoked. Please log in again.",
        )

    @jwt.needs_fresh_token_loader
    def needs_fresh_token_callback(jwt_header, jwt_payload):
        """Endpoint requires a freshly issued token but a stale one was provided."""
        return error_response(
            401,
            "FRESH_TOKEN_REQUIRED",
            "A fresh login is required for this action.",
        )
