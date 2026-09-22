import os

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models import Attachment, JobApplication, User
from app.schemas import AttachmentOut
from app.utils.storage import StorageError, get_storage

router = APIRouter(tags=["attachments"])

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB — generous for resumes/cover letters, safe for free-tier storage


def _get_owned_job_or_404(db: Session, current_user: User, job_id: int) -> JobApplication:
    job = (
        db.query(JobApplication)
        .filter(JobApplication.id == job_id, JobApplication.user_id == current_user.id)
        .first()
    )
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job application not found")
    return job


@router.post(
    "/jobs/{job_id}/attachments", response_model=AttachmentOut, status_code=status.HTTP_201_CREATED
)
def upload_attachment(
    job_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = _get_owned_job_or_404(db, current_user, job_id)

    # Validate size without loading the whole file into memory first.
    file.file.seek(0, os.SEEK_END)
    size = file.file.tell()
    file.file.seek(0)
    if size > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File exceeds the 10MB upload limit",
        )
    if size == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty")

    storage = get_storage()
    try:
        stored = storage.save(file, job_id)
    except StorageError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store attachment: {exc}",
        ) from exc

    attachment = Attachment(
        job_id=job.id,
        filename=file.filename or "unnamed-file",
        filepath=stored.filepath,
        storage_backend=stored.storage_backend,
        content_type=file.content_type,
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)

    out = AttachmentOut.model_validate(attachment)
    out.url = (
        stored.filepath if stored.storage_backend == "cloudinary" else f"/attachments/{attachment.id}/download"
    )
    return out


@router.get("/jobs/{job_id}/attachments", response_model=list[AttachmentOut])
def list_attachments(
    job_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    job = _get_owned_job_or_404(db, current_user, job_id)
    results = []
    for att in job.attachments:
        out = AttachmentOut.model_validate(att)
        out.url = att.filepath if att.storage_backend == "cloudinary" else f"/attachments/{att.id}/download"
        results.append(out)
    return results


def _get_owned_attachment_or_404(db: Session, current_user: User, attachment_id: int) -> Attachment:
    attachment = (
        db.query(Attachment)
        .join(JobApplication)
        .filter(Attachment.id == attachment_id, JobApplication.user_id == current_user.id)
        .first()
    )
    if not attachment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found")
    return attachment


@router.get("/attachments/{attachment_id}/download")
def download_attachment(
    attachment_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    attachment = _get_owned_attachment_or_404(db, current_user, attachment_id)
    if attachment.storage_backend == "cloudinary":
        # Cloudinary URLs are already public/signed; redirect the client there instead.
        from fastapi.responses import RedirectResponse
        return RedirectResponse(attachment.filepath)

    if not os.path.exists(attachment.filepath):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File is missing from storage (this can happen after a redeploy on free-tier "
            "hosts with ephemeral disks — consider switching STORAGE_BACKEND to cloudinary)",
        )
    return FileResponse(attachment.filepath, filename=attachment.filename, media_type=attachment.content_type)


@router.delete("/attachments/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attachment(
    attachment_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    attachment = _get_owned_attachment_or_404(db, current_user, attachment_id)
    storage = get_storage()
    if attachment.storage_backend == settings.STORAGE_BACKEND:
        storage.delete(attachment.filepath)
    db.delete(attachment)
    db.commit()
    return None
