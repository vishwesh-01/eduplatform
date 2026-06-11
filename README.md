# EduPlatform — AI-Powered Personalised Learning

A full-stack education platform that adapts to how you learn. Take a diagnostic quiz, get a personalised course roadmap, watch embedded YouTube lessons, and earn certificates — all powered by the Gemini API.

---

## What it does

When you sign up, you pick a learning goal (like "Python Developer" or "DevOps Engineer"). The platform runs an adaptive quiz that adjusts question difficulty in real time based on your answers, then uses Gemini AI to generate a course list specifically matched to your current skill level. As you complete modules, the path updates again — so you're never stuck on content that's too easy or too hard.

**Core features:**
- Adaptive assessment engine (difficulty 1–5, 5–15 questions, weighted scoring)
- AI-generated personalised learning path via Gemini API
- YouTube videos embedded per module using the YouTube Data API v3
- Real-time progress tracking with streak counter and charts
- Automatic PDF certificate generation on course completion
- Full admin dashboard — user management, role control, AI content audit
- JWT authentication with refresh token rotation and role-based access

---

## Tech stack

| Part | Tech |
|---|---|
| Frontend | React 18, Vite, React Router v6, Axios, Chart.js |
| Backend | Python 3.11+, Flask 3, SQLAlchemy 2, Alembic |
| Database | PostgreSQL 16 |
| AI | Google Gemini API (`gemini-1.5-flash`) |
| Video | YouTube Data API v3 |
| Auth | Flask-JWT-Extended, bcrypt |
| Certs | ReportLab |

---

## Project structure

```
eduplatform/
├── backend/
│   ├── app.py              # Flask app factory
│   ├── config.py           # Config + env var validation
│   ├── extensions.py       # SQLAlchemy, JWT, CORS, Limiter
│   ├── seeds.py            # Seed roles, goals, quiz questions
│   ├── requirements.txt
│   ├── blueprints/
│   │   ├── auth/           # Register, login, JWT refresh
│   │   ├── assessment/     # Adaptive quiz engine
│   │   ├── courses/        # Goals, courses, learning path
│   │   ├── progress/       # Module completion, streak
│   │   ├── certificates/   # List + PDF download
│   │   ├── admin/          # Stats, user management
│   │   ├── ai/             # Gemini service (internal only)
│   │   └── youtube/        # YouTube metadata cache
│   ├── models/             # 16 SQLAlchemy models
│   └── migrations/         # Alembic scripts
├── frontend/
│   └── src/
│       ├── api/            # Axios client + API modules
│       ├── components/     # Navbar, shared UI
│       ├── context/        # AuthContext (JWT state)
│       ├── hooks/          # useAuth
│       └── pages/          # All 12 route pages
├── wsgi.py                 # Entry point for Flask CLI / gunicorn
├── create_db.py            # One-time DB creation helper
├── .env.example            # Template for environment variables
└── plan.md                 # Development roadmap
```

---

## Getting started

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL running locally

### 1. Clone the repo

```bash
git clone https://github.com/vishwesh-01/eduplatform.git
cd eduplatform
```

### 2. Set up environment variables

```bash
copy .env.example .env
```

Open `.env` and fill in:

```env
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/edu_platform
JWT_SECRET_KEY=generate-a-long-random-string
GEMINI_API_KEY=your-gemini-api-key
YOUTUBE_API_KEY=your-youtube-api-key
FLASK_SECRET_KEY=another-random-string
GEMINI_MODEL_NAME=gemini-1.5-flash
```

Generate secure keys with:
```bash
python -c "import secrets; print(secrets.token_hex(64))"
```

### 3. Backend setup

```bash
# Create and activate virtual environment
python -m venv backend/.venv
backend\.venv\Scripts\activate       # Windows
# source backend/.venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r backend/requirements.txt

# Create the database
python create_db.py

# Run migrations
flask --app wsgi db upgrade

# Seed data (roles, goals, 150 quiz questions)
python backend/seeds.py

# Start the server
flask --app wsgi run --debug
```

Backend runs at `http://localhost:5000`

### 4. Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`

---

## Getting API keys

### Gemini API (Google AI Studio)

1. Go to [https://aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. Sign in with your Google account
3. Click **Create API Key** — choose or create a project
4. Copy the key (starts with `AIza...`) into `GEMINI_API_KEY`

> The free tier of `gemini-1.5-flash` is enough for development and personal use.

### YouTube Data API v3

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project (or use an existing one)
3. Go to **APIs & Services → Library**
4. Search for **YouTube Data API v3** and enable it
5. Go to **APIs & Services → Credentials → Create Credentials → API Key**
6. Copy the key into `YOUTUBE_API_KEY`

> The free quota (10,000 units/day) is plenty for development. YouTube metadata is cached in the database after the first fetch.

---

## Making yourself an admin

After registering normally through the frontend, run this in psql:

```sql
-- Get your user ID
SELECT id FROM users WHERE email = 'your@email.com';

-- Get admin role ID
SELECT id FROM roles WHERE name = 'admin';

-- Assign admin role
INSERT INTO user_roles (user_id, role_id)
VALUES ('<your-user-uuid>', <admin-role-id>);
```

Then log out and back in. You'll see the Admin link in the navbar.

---

## Running in production

```bash
# Backend with gunicorn
gunicorn wsgi:app --workers 4 --bind 0.0.0.0:5000

# Frontend build
cd frontend && npm run build
# Serve the dist/ folder with Nginx or deploy to Vercel/Netlify
```

Set `FLASK_ENV=production` in your environment. This enables HTTPS headers and disables debug mode.

---

## Notes

- The `templates/` folder contains the original Jinja2 templates from before the React rewrite. They're kept for reference but not used by the new backend.
- Rate limiting uses in-memory storage by default (fine for dev). For production, configure a Redis backend with Flask-Limiter.
- The `GEMINI_MODEL_NAME` env var lets you switch models without touching code. `gemini-1.5-flash` is recommended for cost and speed.

---

## License

MIT
