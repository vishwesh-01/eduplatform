"""
extensions.py — Flask extension singletons.

Instantiated here without an app context; bound to the app via
their `init_app(app)` method in the create_app() factory.
Importing from this module gives a single instance shared across the app.
"""

from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

# SQLAlchemy ORM instance — used by all models via `db.Model`
db = SQLAlchemy()

# JWT manager — handles token creation, verification, and error callbacks
jwt = JWTManager()

# CORS — configured in create_app() with ALLOWED_ORIGINS from config
cors = CORS()

# Rate limiter — keys requests by remote IP address by default.
# The default_limits list applies to every route unless overridden per-view.
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per minute"])

# Alembic migration manager — tied to db and the app in create_app()
migrate = Migrate()
