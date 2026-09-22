from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import ApplicationStatus, JobApplication, Tag, User
from app.security import hash_password
from app.schemas import JobApplicationCreate, JobApplicationUpdate

STALE_DAYS_THRESHOLD = 14
INTERVIEW_STAGE_STATUSES = {
    ApplicationStatus.phone_screen,
    ApplicationStatus.technical_interview,
    ApplicationStatus.onsite_interview,
    ApplicationStatus.final_interview,
    ApplicationStatus.offer,
}


# ---------- Users ----------

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, email: str, password: str) -> User:
    user = User(email=email, hashed_password=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ---------- Tags ----------

def get_or_create_tags(db: Session, user_id: int, tag_names: list[str]) -> list[Tag]:
    tags = []
    for raw_name in tag_names:
        name = raw_name.strip()
        if not name:
            continue
        tag = (
            db.query(Tag)
            .filter(Tag.user_id == user_id, func.lower(Tag.name) == name.lower())
            .first()
        )
        if not tag:
            tag = Tag(user_id=user_id, name=name)
            db.add(tag)
            db.flush()  # get an ID without a full commit
        tags.append(tag)
    return tags


# ---------- Job Applications ----------

def find_duplicate(db: Session, user_id: int, company_name: str, job_title: str) -> Optional[JobApplication]:
    return (
        db.query(JobApplication)
        .filter(
            JobApplication.user_id == user_id,
            func.lower(JobApplication.company_name) == company_name.strip().lower(),
            func.lower(JobApplication.job_title) == job_title.strip().lower(),
            JobApplication.is_archived.is_(False),
        )
        .first()
    )


def create_job_application(db: Session, user_id: int, payload: JobApplicationCreate) -> JobApplication:
    data = payload.model_dump(exclude={"tag_names", "force_create"})
    job = JobApplication(user_id=user_id, **data)

    if payload.tag_names:
        job.tags = get_or_create_tags(db, user_id, payload.tag_names)

    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def get_job_application(db: Session, user_id: int, job_id: int) -> Optional[JobApplication]:
    return (
        db.query(JobApplication)
        .filter(JobApplication.id == job_id, JobApplication.user_id == user_id)
        .first()
    )


def list_job_applications(
    db: Session,
    user_id: int,
    status: Optional[ApplicationStatus] = None,
    company: Optional[str] = None,
    search: Optional[str] = None,
    tag: Optional[str] = None,
    include_archived: bool = False,
    date_from=None,
    date_to=None,
) -> list[JobApplication]:
    query = db.query(JobApplication).filter(JobApplication.user_id == user_id)

    if not include_archived:
        query = query.filter(JobApplication.is_archived.is_(False))
    if status:
        query = query.filter(JobApplication.status == status)
    if company:
        query = query.filter(func.lower(JobApplication.company_name).contains(company.lower()))
    if search:
        like = f"%{search.lower()}%"
        query = query.filter(
            func.lower(JobApplication.job_title).like(like)
            | func.lower(JobApplication.company_name).like(like)
            | func.lower(func.coalesce(JobApplication.interview_notes, "")).like(like)
        )
    if tag:
        query = query.join(JobApplication.tags).filter(func.lower(Tag.name) == tag.lower())
    if date_from:
        query = query.filter(JobApplication.application_date >= date_from)
    if date_to:
        query = query.filter(JobApplication.application_date <= date_to)

    return query.order_by(JobApplication.updated_at.desc()).all()


def update_job_application(
    db: Session, job: JobApplication, payload: JobApplicationUpdate
) -> JobApplication:
    update_data = payload.model_dump(exclude_unset=True, exclude={"tag_names"})
    for field, value in update_data.items():
        setattr(job, field, value)

    if payload.tag_names is not None:
        job.tags = get_or_create_tags(db, job.user_id, payload.tag_names)

    db.commit()
    db.refresh(job)
    return job


def update_job_status(db: Session, job: JobApplication, status: ApplicationStatus) -> JobApplication:
    job.status = status
    db.commit()
    db.refresh(job)
    return job


def delete_job_application(db: Session, job: JobApplication) -> None:
    db.delete(job)
    db.commit()


def archive_job_application(db: Session, job: JobApplication, archived: bool = True) -> JobApplication:
    job.is_archived = archived
    db.commit()
    db.refresh(job)
    return job


def compute_staleness(job: JobApplication) -> tuple[int, bool]:
    now = datetime.now(timezone.utc)
    updated = job.updated_at
    if updated.tzinfo is None:
        updated = updated.replace(tzinfo=timezone.utc)
    days = (now - updated).days
    is_stale = days >= STALE_DAYS_THRESHOLD and job.status == ApplicationStatus.applied and not job.is_archived
    return days, is_stale


# ---------- Analytics ----------

def get_analytics(db: Session, user_id: int) -> dict:
    all_jobs = (
        db.query(JobApplication)
        .filter(JobApplication.user_id == user_id, JobApplication.is_archived.is_(False))
        .all()
    )
    total = len(all_jobs)
    active = sum(
        1 for j in all_jobs if j.status not in (ApplicationStatus.rejected, ApplicationStatus.withdrawn)
    )

    breakdown: dict[ApplicationStatus, int] = {}
    for j in all_jobs:
        breakdown[j.status] = breakdown.get(j.status, 0) + 1

    interviewed = sum(1 for j in all_jobs if j.status in INTERVIEW_STAGE_STATUSES)
    offers = sum(1 for j in all_jobs if j.status == ApplicationStatus.offer)

    now = datetime.now(timezone.utc)
    last_7 = sum(
        1 for j in all_jobs
        if (now - _as_aware(j.created_at)).days <= 7
    )
    last_30 = sum(
        1 for j in all_jobs
        if (now - _as_aware(j.created_at)).days <= 30
    )
    stale = sum(1 for j in all_jobs if compute_staleness(j)[1])

    return {
        "total_applications": total,
        "active_applications": active,
        "status_breakdown": [{"status": s, "count": c} for s, c in breakdown.items()],
        "interview_rate": round((interviewed / total) * 100, 1) if total else 0.0,
        "offer_rate": round((offers / total) * 100, 1) if total else 0.0,
        "applications_last_7_days": last_7,
        "applications_last_30_days": last_30,
        "stale_applications": stale,
    }


def _as_aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt
