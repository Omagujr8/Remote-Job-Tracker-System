import csv
import io

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.dependencies import get_current_user
from app.models import User

router = APIRouter(prefix="/export", tags=["export"])

CSV_COLUMNS = [
    "id",
    "job_title",
    "company_name",
    "status",
    "application_date",
    "salary_range",
    "location",
    "contact_info",
    "job_url",
    "referred_by",
    "tags",
    "is_archived",
    "created_at",
    "updated_at",
]


@router.get("/csv")
def export_csv(
    include_archived: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    jobs = crud.list_job_applications(db, current_user.id, include_archived=include_archived)

    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=CSV_COLUMNS)
    writer.writeheader()
    for job in jobs:
        writer.writerow(
            {
                "id": job.id,
                "job_title": job.job_title,
                "company_name": job.company_name,
                "status": job.status.value if hasattr(job.status, "value") else job.status,
                "application_date": job.application_date.isoformat(),
                "salary_range": job.salary_range or "",
                "location": job.location or "",
                "contact_info": job.contact_info or "",
                "job_url": job.job_url or "",
                "referred_by": job.referred_by or "",
                "tags": ";".join(t.name for t in job.tags),
                "is_archived": job.is_archived,
                "created_at": job.created_at.isoformat(),
                "updated_at": job.updated_at.isoformat(),
            }
        )
    buffer.seek(0)

    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=job_applications.csv"},
    )
