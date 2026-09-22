# Remote Job Tracker System

A full-stack job application tracker for managing applications, interview stages, notes, tags, attachments, analytics, and weekly email digests.

The project is split into:

- `backend/`: FastAPI, SQLAlchemy, Alembic, and PostgreSQL/SQLite support.
- `frontend/`: React and Vite single-page application.

The backend exposes interactive API documentation at `/docs` while it is running.

## Features

- JWT authentication with bcrypt password hashing.
- User-scoped job application CRUD and cross-user data isolation.
- Kanban status updates, archive/unarchive, duplicate detection, search, filters, and tags.
- Attachment upload/download with local development storage and an optional Cloudinary backend.
- Analytics, CSV export, URL-based quick add, and optional weekly email digests.

## Prerequisites

- Python 3.11 or newer.
- Node.js 18 or newer and npm.
- Git.

## Local setup on Windows

Open PowerShell in the repository root.

### Backend

```powershell
Set-Location backend
py -3.11 -m venv .venv
\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `backend/.env` before running the application. For local development, SQLite is sufficient. Generate a private signing key instead of keeping the example value:

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

Place the generated value in `SECRET_KEY`. Then run migrations and start the API:

```powershell
alembic upgrade head
uvicorn app.main:app --reload
```

The API is available at `http://localhost:8000` and its Swagger UI is at `http://localhost:8000/docs`.

### Frontend

Open a second PowerShell window:

```powershell
Set-Location frontend
npm install
Copy-Item .env.example .env
npm run dev
```

The frontend is available at `http://localhost:5173`. Keep `VITE_API_URL=http://localhost:8000` in `frontend/.env` unless the API uses another URL.

## Checks

Backend tests:

```powershell
Set-Location backend
\.venv\Scripts\Activate.ps1
pytest
```

Frontend tests and production build:

```powershell
Set-Location frontend
npm test
npm run build
```

## Configuration

Use the committed templates as the source of variable names:

- [Backend environment template](backend/.env.example)
- [Frontend environment template](frontend/.env.example)

Never commit a populated `.env` file. Production secrets belong in the hosting provider's environment-variable settings. See the component-specific documentation for the complete API, deployment, and storage details: [backend README](backend/README.md) and [frontend README](frontend/README.md).

## Publish safely to GitHub

This workspace currently has no project-level Git repository. From the repository root:

```powershell
git init
git branch -M main
git add .gitignore README.md backend frontend
git status --short
```

Read the `git status` output carefully. It should not contain `.env`, `*.db`, `backend/uploads/` documents, `node_modules/`, `.venv/`, or production credentials. If a sensitive file appears, do not commit it. Remove it from the staging area with `git restore --staged path\to\file` and add an ignore rule before continuing.

Once the staged file list is clean:

```powershell
git commit -m "docs: prepare project for GitHub"
git remote add origin https://github.com/<your-account>/<your-repository>.git
git push -u origin main
```

### Secret-safety checklist

1. Keep `backend/.env` and `frontend/.env` local. Commit only `.env.example` files containing placeholders.
2. Do not commit resumes, cover letters, exported CSVs, local databases, logs, screenshots with personal data, or API tokens.
3. Generate a new `SECRET_KEY` for every environment. Do not reuse a key that has appeared in a public commit.
4. Use GitHub secret scanning and push protection if available for the repository.
5. Review the staged file list before every first push and before publishing a release.
6. If a secret was ever committed, rotate/revoke it immediately. Removing the file in a later commit is not enough; rewrite history with a dedicated tool such as `git filter-repo` only after rotating the credential.

To confirm that local files are ignored before staging:

```powershell
git check-ignore -v backend/.env frontend/.env backend/job_tracker.db backend/uploads/example.pdf frontend/node_modules
```

## Suggested Git workflow

Use small, focused commits such as `feat: add kanban status updates`, `fix: isolate attachments by user`, or `docs: update deployment steps`. Use pull requests for changes once the repository is shared, and keep deployment secrets in Render, Railway, Vercel, or the relevant provider rather than in GitHub.

## License

No license has been selected yet. Choose a license before presenting this as an open-source project.