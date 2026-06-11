"""
config.py — Flask application configuration classes.

Reads all runtime settings from environment variables. If any critical
variable is missing at startup, logs a CRITICAL message and exits with
status code 1 so the process manager knows to restart/alert.

Critical variables (must be present):
  - DATABASE_URL
  - JWT_SECRET_KEY
  - GEMINI_API_KEY
  - YOUTUBE_API_KEY
"""

import logging
import os
import sys

from dotenv import load_dotenv

load_dotenv()  # Load .env file if present

logger = logging.getLogger(__name__)

# ── Critical variable validation ────────────────────────────────────────────
CRITICAL_VARS = ["DATABASE_URL", "JWT_SECRET_KEY", "GEMINI_API_KEY", "YOUTUBE_API_KEY"]


def validate_critical_env():
    """
    Check that all critical environment variables are set.
    Logs a CRITICAL message for each missing variable and exits with
    status code 1 if any are absent. Both the log AND the exit are required.
    """
    missing = [var for var in CRITICAL_VARS if not os.environ.get(var)]
    if missing:
        for var in missing:
            logger.critical(f"Missing required environment variable: {var}")
        sys.exit(1)


class Config:
    """Base configuration shared across all environments."""

    # Flask core
    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "fallback-dev-key")
    ENV = os.environ.get("FLASK_ENV", "development")

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,          # detect stale connections before use
        "pool_recycle": 300,            # recycle connections after 5 min to avoid timeout drops
        "connect_args": {"connect_timeout": 10},
    }

    # JWT — access tokens are short-lived; refresh tokens last longer
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "")
    JWT_ACCESS_TOKEN_EXPIRES_MINUTES = 15
    JWT_REFRESH_TOKEN_EXPIRES_DAYS = 7

    # External API keys
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
    GEMINI_MODEL_NAME = os.environ.get("GEMINI_MODEL_NAME", "gemma-3-27b-it")
    YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "")

    # CORS — split comma-separated origins; filter blanks
    ALLOWED_ORIGINS = [
        o.strip()
        for o in os.environ.get("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
        if o.strip()
    ]

    # Reject request bodies larger than 1 MB (Flask raises 413 automatically)
    MAX_CONTENT_LENGTH = 1 * 1024 * 1024

    # Logging level — overridden per environment below
    LOG_LEVEL = logging.DEBUG


class DevelopmentConfig(Config):
    """Development environment — verbose logging, debug mode enabled."""

    DEBUG = True
    TESTING = False
    LOG_LEVEL = logging.DEBUG


class ProductionConfig(Config):
    """Production environment — no debug output, INFO-level logging."""

    DEBUG = False
    TESTING = False
    LOG_LEVEL = logging.INFO


class TestingConfig(Config):
    """
    Test environment — uses a separate test database so tests never
    touch the development or production database.
    """

    TESTING = True
    DEBUG = True
    # Allow tests to override the DB URL; default points at a local test DB
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "TEST_DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/edu_platform_test",
    )


# Map environment name strings → config classes.
# Used by create_app() to select the right class via FLASK_ENV.
config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}
