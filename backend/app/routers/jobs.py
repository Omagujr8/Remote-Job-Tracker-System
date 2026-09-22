from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.dependencies import get_current_user
from app.models import ApplicationStatus, User
from app.schemas import (
    DuplicateWarning,
    JobApplicationCreate,
    JobApplicationOut,
    JobApplicationUpdate,
    QuickAddFromUrlRequest,
    QuickAddFromUrlResponse,
    StatusUpdate,
)
from app.utils.scraping import extract_job_metadata

router = APIRouter(prefix="/jobs", tags=["jobs"])


def _to_out(job) -> JobApplicationOut:
    """Attach computed staleness fields before serializing."""
    days, is_stale = crud.compute_staleness(job)
    out = JobApplicationOut.model_validate(job)
    out.days_since_update = days
    out.is_stale = is_stale
    for att, model_att in zip(out.attachments, job.attachments):
        att.url = f"/attachments/{model_att.id}/download"
    return out


@router.get("/check-duplicate", response_model=DuplicateWarning)
def check_duplicate(
    company_name: str,
    job_title: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = crud.find_duplicate(db, current_user.id, company_name, job_title)
    if existing:
        return DuplicateWarning(
            duplicate_found=True,
            existing_job_id=existing.id,
            message=(
                f"You already have an application for '{existing.job_title}' at "
                f"'{existing.company_name}' (added {existing.created_at.date()})."
            ),
        )
    return DuplicateWarning(duplicate_found=False)


@router.post("", response_model=JobApplicationOut, status_code=status.HTTP_201_CREATED)
def create_job(
    payload: JobApplicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not payload.force_create:
        existing = crud.find_duplicate(db, current_user.id, payload.company_name, payload.job_title)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "message": (
                        f"A matching application already exists (id={existing.id}). "
                        "Resubmit with force_create=true to add it anyway."
                    ),
                    "existing_job_id": existing.id,
                },
            )
    try:
        job = crud.create_job_application(db, current_user.id, payload)
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save job application due to a database error",
        ) from exc
    return _to_out(job)


@router.get("", response_model=list[JobApplicationOut])
def list_jobs(
    status_filter: Optional[ApplicationStatus] = None,
    company: Optional[str] = None,
    search: Optional[str] = None,
    tag: Optional[str] = None,
    include_archived: bool = False,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    jobs = crud.list_job_applications(
        db,
        current_user.id,
        status=status_filter,
        company=company,
        search=search,
        tag=tag,
        include_archived=include_archived,
        date_from=date_from,
        date_to=date_to,
    )
    return [_to_out(j) for j in jobs]


def _get_owned_job_or_404(db: Session, current_user: User, job_id: int):
    job = crud.get_job_application(db, current_user.id, job_id)
    if not job:
        # Deliberately generic message: don't reveal whether the job exists
        # for another user, to avoid leaking cross-account information.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job application not found")
    return job


@router.get("/{job_id}", response_model=JobApplicationOut)
def get_job(job_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    job = _get_owned_job_or_404(db, current_user, job_id)
    return _to_out(job)


@router.put("/{job_id}", response_model=JobApplicationOut)
@router.patch("/{job_id}", response_model=JobApplicationOut)
def update_job(
    job_id: int,
    payload: JobApplicationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = _get_owned_job_or_404(db, current_user, job_id)
    try:
        job = crud.update_job_application(db, job, payload)
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update job application due to a database error",
        ) from exc
    return _to_out(job)


@router.patch("/{job_id}/status", response_model=JobApplicationOut)
def update_status(
    job_id: int,
    payload: StatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Dedicated lightweight endpoint for kanban drag-and-drop / quick status changes."""
    job = _get_owned_job_or_404(db, current_user, job_id)
    job = crud.update_job_status(db, job, payload.status)
    return _to_out(job)


@router.patch("/{job_id}/archive", response_model=JobApplicationOut)
def archive_job(
    job_id: int,
    archived: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = _get_owned_job_or_404(db, current_user, job_id)
    job = crud.archive_job_application(db, job, archived)
    return _to_out(job)


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(job_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    job = _get_owned_job_or_404(db, current_user, job_id)
    try:
        crud.delete_job_application(db, job)
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete job application due to a database error",
        ) from exc
    return None


@router.post("/quick-add-from-url", response_model=QuickAddFromUrlResponse)
def quick_add_from_url(
    payload: QuickAddFromUrlRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Best-effort metadata extraction from a pasted job posting URL.
    This never creates a job on its own — it returns pre-filled suggestions
    for the frontend form, which the user then reviews and submits normally
    via POST /jobs. This keeps a bad scrape from ever silently corrupting data.
    """
    metadata = extract_job_metadata(payload.url)
    return QuickAddFromUrlResponse(
        job_title=metadata.get("job_title"),
        company_name=metadata.get("company_name"),
        job_url=payload.url,
        note=metadata.get("note", ""),
    )
