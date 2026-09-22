import enum

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class ApplicationStatus(str, enum.Enum):
    applied = "applied"
    phone_screen = "phone_screen"
    technical_interview = "technical_interview"
    onsite_interview = "onsite_interview"
    final_interview = "final_interview"
    offer = "offer"
    rejected = "rejected"
    withdrawn = "withdrawn"


# Many-to-many association between job applications and tags.
job_tags = Table(
    "job_tags",
    Base.metadata,
    Column("job_id", Integer, ForeignKey("job_applications.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    job_applications = relationship(
        "JobApplication", back_populates="owner", cascade="all, delete-orphan"
    )
    tags = relationship("Tag", back_populates="owner", cascade="all, delete-orphan")


class JobApplication(Base):
    __tablename__ = "job_applications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    job_title = Column(String(255), nullable=False)
    company_name = Column(String(255), nullable=False)
    status = Column(
        Enum(ApplicationStatus, native_enum=False, length=32),
        nullable=False,
        default=ApplicationStatus.applied,
        index=True,
    )
    application_date = Column(Date, nullable=False)

    # Detailed tracking fields
    salary_range = Column(String(120), nullable=True)
    location = Column(String(255), nullable=True)
    contact_info = Column(String(500), nullable=True)
    interview_notes = Column(Text, nullable=True)

    # Extra fields from the confirmed feature set
    job_url = Column(String(1000), nullable=True)
    referred_by = Column(String(255), nullable=True)
    is_archived = Column(Boolean, default=False, nullable=False, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    owner = relationship("User", back_populates="job_applications")
    tags = relationship("Tag", secondary=job_tags, back_populates="job_applications")
    attachments = relationship(
        "Attachment", back_populates="job_application", cascade="all, delete-orphan"
    )


class Tag(Base):
    __tablename__ = "tags"
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_tag_per_user"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(50), nullable=False)

    owner = relationship("User", back_populates="tags")
    job_applications = relationship("JobApplication", secondary=job_tags, back_populates="tags")


class Attachment(Base):
    __tablename__ = "attachments"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(
        Integer, ForeignKey("job_applications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    filename = Column(String(255), nullable=False)
    # For "local" backend: relative path on disk. For "cloudinary": the secure_url.
    filepath = Column(String(1000), nullable=False)
    storage_backend = Column(String(20), nullable=False, default="local")
    content_type = Column(String(120), nullable=True)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    job_application = relationship("JobApplication", back_populates="attachments")
