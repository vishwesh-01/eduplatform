"""
wsgi.py — WSGI / Flask CLI entry point.

ALWAYS run Flask commands from the project root (eduplatform/) directory:

    Development server:
        flask --app wsgi run --debug

    Database migrations:
        flask --app wsgi db init          (first time only — skip if migrations/ exists)
        flask --app wsgi db migrate -m "initial schema"
        flask --app wsgi db upgrade

    Seed data:
        python backend/seeds.py

    Production:
        gunicorn wsgi:app --workers 4 --bind 0.0.0.0:5000
"""

from backend.app import create_app

# Create the application instance — used by Flask CLI and gunicorn
app = create_app()

if __name__ == "__main__":
    app.run()
