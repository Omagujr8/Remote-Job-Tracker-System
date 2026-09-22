# M4 Remote Job Tracker — Backend

A multi-user job application tracker API built with **FastAPI + SQLAlchemy + PostgreSQL** (SQLite for local dev). This is the backend half of the M4 Remote Job Tracker System — the frontend (React) consumes this API.

## Features implemented

**Core**
- JWT authentication (register/login), bcrypt password hashing
- Full CRUD on job applications, strictly scoped per authenticated user
- Dedicated status-update endpoint (for kanban drag-and-drop)
- Persistent storage via SQLAlchemy + Alembic migrations

**Additional**
- Search, filter (status/company/date range/tag), and combined queries
- Tags (many-to-many, per-user)
- File attachments (resumes/cover letters) with a swappable storage backend (local disk for dev, Cloudinary for production)
- Analytics endpoint (interview rate, offer rate, status breakdown, stale-application count)
- CSV export
- Archive (soft-delete) instead of destructive-only deletes
- Duplicate-application detection with an override
- Interview-round-aware status enum (phone screen → technical → onsite → final → offer)
- Job posting URL + referred-by fields
- "Quick add from URL" best-effort metadata scraper
- Staleness indicator (computed `days_since_update` / `is_stale` on every job)
- Weekly email digest, triggered externally (see below) — degrades gracefully if SMTP isn't configured

## Project structure

```
app/
  main.py              FastAPI app, router wiring, CORS, error handlers
  config.py            Settings (env vars)
  database.py          SQLAlchemy engine/session
  models.py            ORM models (User, JobApplication, Tag, Attachment)
  schemas.py           Pydantic request/response models
  security.py          Password hashing + JWT
  dependencies.py      get_current_user auth dependency
  crud.py              Database operations
  routers/
    auth.py            register, login, /me
    jobs.py            CRUD, status, archive, duplicate check, quick-add-from-url
    tags.py            list/delete tags
    attachments.py     upload/list/download/delete files
    analytics.py        stats endpoint
    export.py           CSV export
    digest.py            weekly email digest trigger
  utils/
    storage.py          local/Cloudinary storage abstraction
    scraping.py          job-URL metadata extraction
alembic/                 DB migrations
tests/                   pytest suite (39 tests: auth, CRUD, isolation, attachments)
```

## Local setup

**Requirements:** Python 3.11+

```bash
git clone <your-repo-url>
cd m4-job-tracker-backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` — for local dev the defaults work as-is (SQLite, no external services needed). At minimum, set a real `SECRET_KEY`:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Apply migrations and run the server:

```bash
alembic upgrade head
uvicorn app.main:app --reload
```

The API is now live at `http://localhost:8000`. Interactive docs: `http://localhost:8000/docs`.

## Running tests

```bash
pytest
```

39 tests cover: registration/login validation, auth-required routes, full CRUD, status transitions, duplicate detection, archive/unarchive, filtering/search/tags, **cross-user data isolation** (the multi-tenant safety net), attachment upload/download/isolation, and analytics.

## Environment variables

See `.env.example` for the full list with comments. Key ones:

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | SQLite locally, Postgres in production |
| `SECRET_KEY` | JWT signing key — must be a real secret in production |
| `CORS_ORIGINS` | Comma-separated frontend origin(s) allowed to call the API |
| `STORAGE_BACKEND` | `local` or `cloudinary` |
| `SMTP_*` | Optional — enables the weekly digest email |
| `DIGEST_TRIGGER_SECRET` | Shared secret protecting the digest trigger endpoint |

## Deployment (Render free tier)

1. **Push this repo to GitHub** (see Git workflow below).
2. **Create a Postgres database** on Render (free tier) — copy its "Internal Database URL".
3. **Create a new Web Service** on Render, connect your GitHub repo:
   - Build command: `pip install -r requirements.txt`
   - Start command: `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. **Set environment variables** in Render's dashboard: `DATABASE_URL` (the Postgres URL from step 2), `SECRET_KEY`, `CORS_ORIGINS` (your deployed frontend's URL once it exists), and optionally the storage/SMTP vars.
5. Deploy. Render builds and starts the service; `alembic upgrade head` runs the migrations against your Postgres DB automatically on every deploy.
6. **(Optional) Weekly digest**: Render's free tier includes Cron Jobs — create one that runs weekly and does:
   ```bash
   curl -X POST https://your-api.onrender.com/digest/send-weekly -H "x-digest-secret: $DIGEST_TRIGGER_SECRET"
   ```
7. **(Optional) Persistent attachments**: free-tier disks are ephemeral (wiped on redeploy). Sign up for Cloudinary's free tier, set `STORAGE_BACKEND=cloudinary` plus the `CLOUDINARY_*` vars, and `pip install cloudinary` (add it to `requirements.txt`) — no code changes needed elsewhere.

Railway free tier works the same way (Postgres plugin + a service pointed at this repo with the same build/start commands).

## Git workflow for the 2–3 week build

Suggested commit cadence as we co-develop:

- **One feature/module per commit** — e.g. `feat: JWT auth + user registration`, `feat: job CRUD endpoints`, `feat: attachment upload with storage abstraction`, `test: cross-user isolation suite`.
- **Commit after each working checkpoint**, not just at the end of a session — small, working, pushed commits mean we can always roll back to a known-good state.
- Suggested branch pattern for a solo/co-dev cycle: work on `main` directly for backend scaffolding (low risk, this is greenfield), but once the frontend is live and deployed, use short-lived feature branches (`feat/kanban-view`, `fix/status-bug`) merged via PR — gives you a changelog and a safety net once real data exists.
- Tag milestones: `v0.1-backend-core`, `v0.2-backend-complete`, `v1.0-deployed`.
- Keep `.env` out of git (already in `.gitignore`) — only `.env.example` is committed.

Example initial push:

```bash
git init
git add .
git commit -m "feat: initial FastAPI backend — auth, job CRUD, tags, attachments, analytics"
git branch -M main
git remote add origin <your-repo-url>
git push -u origin main
```

## API overview

| Method | Path | Purpose |
|---|---|---|
| POST | `/auth/register` | Create account |
| POST | `/auth/login` | Get JWT |
| GET | `/auth/me` | Current user |
| POST | `/jobs` | Create application (409 on duplicate unless `force_create`) |
| GET | `/jobs` | List (filters: `status_filter`, `company`, `search`, `tag`, `include_archived`, `date_from`, `date_to`) |
| GET | `/jobs/{id}` | Get one |
| PATCH | `/jobs/{id}` | Partial update |
| PATCH | `/jobs/{id}/status` | Status-only update (kanban) |
| PATCH | `/jobs/{id}/archive` | Archive/unarchive |
| DELETE | `/jobs/{id}` | Hard delete |
| GET | `/jobs/check-duplicate` | Pre-flight duplicate check |
| POST | `/jobs/quick-add-from-url` | Scrape suggestions from a pasted URL |
| GET | `/tags` / `DELETE /tags/{id}` | Manage tags |
| POST | `/jobs/{id}/attachments` | Upload file |
| GET | `/jobs/{id}/attachments` | List files for a job |
| GET | `/attachments/{id}/download` | Download a file |
| DELETE | `/attachments/{id}` | Delete a file |
| GET | `/analytics` | Stats summary |
| GET | `/export/csv` | CSV export |
| POST | `/digest/send-weekly` | Trigger weekly emails (cron only, secret-protected) |

Full interactive schema always available at `/docs` once running.

## What's next (frontend)

This backend is feature-complete for the confirmed scope. Next step: scaffold the React frontend (Vite) — auth pages, kanban/list dashboard, job form, and wire it to this API via `CORS_ORIGINS`.
