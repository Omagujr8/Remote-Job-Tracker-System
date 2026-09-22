# M4 Remote Job Tracker — Frontend

React + Vite frontend for the M4 Remote Job Tracker. Talks to the FastAPI backend over REST; ships as a static site.

## Design

"Field Log" visual identity — the job hunt as an expedition log rather than a generic SaaS dashboard. Pine-green + gold palette, Fraunces (serif display) + IBM Plex Sans (UI), flat index-card style kanban cards instead of the default rounded-card-with-shadow look.

## Features implemented

- Auth (login/register), session persistence via JWT in localStorage
- **Kanban board** (drag-and-drop status changes) grouping the four interview sub-stages under one "Interviewing" column
- **List view** with search, status filter, tag filter, archive toggle, CSV export
- **Job detail page**: view/edit, dedicated status-change control, notes, tags, file attachments (upload/download/delete), archive/unarchive, delete with confirmation
- **Quick-add from URL**: paste a job posting link to prefill title/company, with duplicate-application warning and override
- **Analytics page**: interview rate, offer rate, status breakdown, staleness count
- Staleness indicator surfaced on cards and the detail page

## Local setup

**Requirements:** Node 18+

```bash
cd m4-job-tracker-frontend
npm install
cp .env.example .env
```

Edit `.env` to point at your backend (defaults to `http://localhost:8000`, matching the backend's default local port):

```
VITE_API_URL=http://localhost:8000
```

Run the dev server:

```bash
npm run dev
```

Opens at `http://localhost:5173`. Make sure the backend's `CORS_ORIGINS` includes this URL (it does by default in the backend's `.env.example`).

## Running tests

```bash
npm test
```

14 tests covering: API client auth-header injection and error handling, `AuthContext` session restore/login/register/logout, and `ProtectedRoute` redirect behavior.

## Building for production

```bash
npm run build
```

Outputs a static site to `dist/`.

## Deployment (Vercel free tier)

1. Push this repo to GitHub.
2. On [vercel.com](https://vercel.com), "Add New Project" → import the repo.
3. Vercel auto-detects Vite; defaults (`npm run build`, output dir `dist`) work as-is.
4. Add an environment variable in the Vercel project settings: `VITE_API_URL` = your deployed backend's URL (e.g. `https://your-api.onrender.com`).
5. Deploy. Every push to `main` triggers a new deployment; every other branch/PR gets its own preview URL.
6. Once deployed, go back to the backend's `CORS_ORIGINS` env var on Render/Railway and add this Vercel URL, then redeploy the backend so it accepts requests from the live frontend.

## Project structure

```
src/
  api/client.js          Fetch wrapper: auth headers, typed errors, blob downloads
  context/AuthContext.jsx Session state (login/register/logout)
  components/            Layout, JobCard, KanbanBoard, JobForm, StatusBadge,
                          TagInput, ConfirmDialog, EmptyState, ProtectedRoute
  pages/                 LoginPage, RegisterPage, DashboardPage (kanban),
                          ListPage, NewJobPage, JobDetailPage, AnalyticsPage
  statusMeta.js           Shared status labels/colors/kanban column mapping
  styles/global.css       Design tokens + shared UI primitives
```

## Git workflow

Same cadence as the backend — small, working commits per feature:

```bash
git add .
git commit -m "feat: kanban board with drag-and-drop status updates"
git push
```

Suggested milestones: `v0.1-frontend-auth`, `v0.2-frontend-core-crud`, `v1.0-deployed`.

## Known trade-offs (by design, not oversights)

- **CSV export and attachment downloads** use an authenticated `fetch` + blob trick rather than plain `<a href>` links, because those endpoints require a Bearer token that a static link can't send.
- **Quick-add-from-URL** degrades gracefully: many job boards block simple scrapers or require JS rendering, so a failed scrape just leaves the form blank for manual entry rather than erroring out.
- **JWT in localStorage** (not an httpOnly cookie) — simplest approach for a free-tier, cross-origin (Vercel ↔ Render) setup where frontend and backend live on different domains. Acceptable for this project's threat model; worth revisiting with refresh-token rotation if this becomes a public multi-tenant product with more at stake.
