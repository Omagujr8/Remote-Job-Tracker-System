from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, ConfigDict

from app.models import ApplicationStatus


# ---------- Auth / User ----------

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------- Tags ----------

class TagCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)


class TagOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


# ---------- Attachments ----------

class AttachmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    filename: str
    content_type: Optional[str] = None
    uploaded_at: datetime
    url: Optional[str] = None  # populated by the router (local path or Cloudinary URL)


# ---------- Job Applications ----------

class JobApplicationBase(BaseModel):
    job_title: str = Field(min_length=1, max_length=255)
    company_name: str = Field(min_length=1, max_length=255)
    status: ApplicationStatus = ApplicationStatus.applied
    application_date: date
    salary_range: Optional[str] = Field(default=None, max_length=120)
    location: Optional[str] = Field(default=None, max_length=255)
    contact_info: Optional[str] = Field(default=None, max_length=500)
    interview_notes: Optional[str] = None
    job_url: Optional[str] = Field(default=None, max_length=1000)
    referred_by: Optional[str] = Field(default=None, max_length=255)


class JobApplicationCreate(JobApplicationBase):
    tag_names: list[str] = Field(default_factory=list)
    # If True, bypass the duplicate-detection warning and create anyway.
    force_create: bool = False


class JobApplicationUpdate(BaseModel):
    """All fields optional — supports partial updates (PATCH semantics)."""
    job_title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    company_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    status: Optional[ApplicationStatus] = None
    application_date: Optional[date] = None
    salary_range: Optional[str] = Field(default=None, max_length=120)
    location: Optional[str] = Field(default=None, max_length=255)
    contact_info: Optional[str] = Field(default=None, max_length=500)
    interview_notes: Optional[str] = None
    job_url: Optional[str] = Field(default=None, max_length=1000)
    referred_by: Optional[str] = Field(default=None, max_length=255)
    is_archived: Optional[bool] = None
    tag_names: Optional[list[str]] = None


class StatusUpdate(BaseModel):
    """Dedicated lightweight payload for the quick status-change action / kanban drag."""
    status: ApplicationStatus


class JobApplicationOut(JobApplicationBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    tags: list[TagOut] = []
    attachments: list[AttachmentOut] = []
    days_since_update: int = 0  # computed by the router for the staleness indicator
    is_stale: bool = False      # true if days_since_update >= 14 and status is still "applied"


class DuplicateWarning(BaseModel):
    duplicate_found: bool
    existing_job_id: Optional[int] = None
    message: Optional[str] = None


# ---------- URL quick-add ----------

class QuickAddFromUrlRequest(BaseModel):
    url: str


class QuickAddFromUrlResponse(BaseModel):
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    job_url: str
    note: str


# ---------- Analytics ----------

class StatusCount(BaseModel):
    status: ApplicationStatus
    count: int


class AnalyticsOut(BaseModel):
    total_applications: int
    active_applications: int  # not archived, not rejected/withdrawn
    status_breakdown: list[StatusCount]
    interview_rate: float  # % of applications that reached at least phone_screen
    offer_rate: float      # % of applications that reached offer
    applications_last_7_days: int
    applications_last_30_days: int
    stale_applications: int
