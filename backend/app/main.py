import logging

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exception_handlers import http_exception_handler
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.config import settings
from app.database import Base, engine
from app.routers import analytics, attachments, auth, digest, export, jobs, tags

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("m4_job_tracker")

# Create tables automatically for quick local dev / SQLite.
# In production with Postgres, prefer running Alembic migrations instead
# (see README) so schema changes are tracked — this call is a harmless no-op
# once migrations have already created the tables.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="M4 Remote Job Tracker API",
    description="Multi-user job application tracker backend.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(jobs.router)
app.include_router(tags.router)
app.include_router(attachments.router)
app.include_router(analytics.router)
app.include_router(export.router)
app.include_router(digest.router)


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.error("Unhandled database error on %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "A database error occurred. Please try again."},
    )


@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    # Keep FastAPI's default behavior but ensure consistent logging.
    if exc.status_code >= 500:
        logger.error("HTTP %s on %s %s: %s", exc.status_code, request.method, request.url.path, exc.detail)
    return await http_exception_handler(request, exc)


@app.get("/", tags=["health"])
def health_check():
    return {"status": "ok", "service": "M4 Remote Job Tracker API"}
