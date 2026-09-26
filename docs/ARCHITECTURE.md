# CampusPulse architecture

## Request and data flow

React pages → typed frontend API client → authenticated FastAPI routes → SQLAlchemy services → SQLite / file storage

The browser stores the bearer token through the session service. Protected API routes resolve the current student from that token; services and queries scope private records by that student ID. The frontend router is client-side and Vercel serves index.html for app routes using frontend/vercel.json. /api is deliberately excluded from that rewrite because the API runs on a separate origin.

## Feature ownership

| Area | Backend boundaries | Source of truth |
|---|---|---|
| Accounts and profile | api/routes/auth.py, services/auth_service.py | students |
| Semesters and academic history | api/routes/semesters.py, services/semester_service.py | semesters, semester_courses |
| Courses, enrollment, marks | corresponding route/service modules | courses, enrollments, course_marks |
| Grades and GPA | services/academic/, services/academic_service.py | configured grading bands, weighted assessments, course credits |
| Attendance, exams, assignments | route/service modules of the same names | student-owned tables |
| Analytics and insights | api/routes/analytics.py, services/analytics_service.py | derived from academic and planning records |
| Targets and what-if | api/routes/planning.py, services/planning_service.py | academic_targets, what_if_scenarios |
| Documents | api/routes/documents.py, document services and storage adapter | document metadata/chunks and uploaded files |
| Assistant | api/routes/ai.py, AI service/provider boundary | conversation records; deterministic provider is default |

## GPA and scenarios

Assessment scores are normalized and weighted by the course's grading scheme. The existing grade-band and GPA engines calculate letter grades, grade points, semester GPA, and cumulative GPA. Scenario preview merges hypothetical assessment inputs with saved marks in memory, then invokes the same score and GPA engines; it does not write hypothetical marks into course_marks. Saved scenarios persist only owner-scoped input values. Targets report INSUFFICIENT_DATA when the relevant calculated GPA is unavailable.

SGPA targets refer to the current semester. Scenario values are projections from the current workspace state and are recalculated when read.

## Security and persistence

- Protected resources are tied to the authenticated student, with ownership checks in backend routes/services.
- Passwords are stored as hashes; bearer tokens can be revoked by incrementing a token version.
- CORS is configured with CORS_ORIGINS; secrets and runtime .env files are not source-controlled.
- Database initialization is incremental and refuses a malformed legacy identity table instead of deleting it.
- SQLite and local document files persist on disk only when the host provides durable storage. Ephemeral service filesystems can lose data after restart/redeploy; hosted durability must be verified with the deployment configuration.

## Deployment boundaries

The frontend and API are separate deployments. Set frontend VITE_API_BASE_URL at build time to the backend origin. Set backend CORS_ORIGINS to the frontend origin. Vercel Root Directory is frontend; its SPA fallback rewrites non-API routes to index.html. No paid AI, auth, database, or vector service is required by the default architecture.
