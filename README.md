# CampusPulse

CampusPulse is a personal academic workspace for managing semesters, courses, assessments, grades, attendance, exams, assignments, documents, analytics, GPA targets, and deterministic what-if scenarios.

## Stack

- Frontend: React, TypeScript, Vite, Tailwind CSS, React Router
- Backend: FastAPI, SQLAlchemy, Pydantic
- Database: SQLite by default
- Assistant: deterministic responses by default; no paid AI provider is required

## Local development

Requirements: Node.js/npm and Python 3.11 or newer.

1. Copy backend/.env.example to backend/.env. Set JWT_SECRET_KEY to a random secret of at least 32 characters. Keep .env files private.
2. Create and activate a Python virtual environment inside backend, then run pip install -r requirements.txt.
3. Start the API from backend with python -m uvicorn app.main:app --reload. The API listens on http://127.0.0.1:8000; interactive API docs are at /docs.
4. Copy frontend/.env.example to frontend/.env if needed, install frontend packages with npm install, and start Vite with npm run dev.
5. Register a user in the app. Each authenticated account gets an owner-scoped workspace.

The default SQLite database is backend/campuspulse.db; uploaded files are stored under backend/storage/uploads. Both are local runtime data and excluded from version control.

## Production configuration

- Deploy the Vite app with Vercel Root Directory set to frontend. frontend/vercel.json routes application pages to index.html while excluding /api paths. The backend is a separate service.
- Configure Vercel build variable VITE_API_BASE_URL to the deployed backend origin, for example https://campuspulse-backend-k45x.onrender.com. The production bundle does not silently fall back to localhost.
- Configure backend CORS_ORIGINS to include the exact frontend origin, such as https://campuspulse-mu.vercel.app.
- Set a private, random JWT_SECRET_KEY and review storage/database paths in the backend deployment environment.

SQLite on an ephemeral hosting filesystem is not durable across service restarts, redeploys, or sleep cycles. Confirm the backend host's current storage/disk arrangement before treating hosted records or uploaded files as durable. This project does not require a paid database; reliable free production persistence depends on the selected host's current free-tier capabilities.

## SQLite backup and recovery

The default database file is backend/campuspulse.db. For a consistent manual backup while the backend may be running, use Python's SQLite backup API from the repository root:

python -c "import sqlite3; source=sqlite3.connect('backend/campuspulse.db'); target=sqlite3.connect('backend/campuspulse-backup.db'); source.backup(target); target.close(); source.close()"

Keep the backup outside public deployments and verify it with a copy of the app before relying on it. To restore, stop the backend first, preserve a copy of the current database, replace backend/campuspulse.db with the verified backup, then start the backend and inspect the workspace. Back up backend/storage/uploads separately when uploaded files matter; database backups do not contain those files. On ephemeral hosts, copy backups off the service filesystem because local files can disappear on restart or redeploy.

## Checks

From backend: .venv/Scripts/python.exe -m pytest on Windows, or python -m pytest.

From frontend: npm run build and npm run lint.

See docs/ARCHITECTURE.md for application boundaries, data flow, security, and feature inventory.
