"""
Weekly digest emails.

Free-tier hosts don't reliably support long-running background schedulers
(the process can sleep/spin down). So instead of an in-process cron, this
exposes ONE endpoint that does "send today's digests to everyone due for
one" and is meant to be triggered by an external, free scheduler — e.g.
Render's free Cron Jobs, or a GitHub Actions scheduled workflow hitting
this URL once a day/week.

The endpoint is protected by a shared secret (DIGEST_TRIGGER_SECRET) rather
than user auth, since it's called by a machine, not a logged-in user.
"""
import smtplib
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText

from fastapi import APIRouter, Header, HTTPException, status
from sqlalchemy.orm import Session

from app import crud
from app.config import settings
from app.database import SessionLocal
from app.models import User

router = APIRouter(prefix="/digest", tags=["digest"])


def _build_digest_body(email: str, analytics: dict) -> str:
    breakdown_lines = "\n".join(
        f"  - {row['status'].value if hasattr(row['status'], 'value') else row['status']}: {row['count']}"
        for row in analytics["status_breakdown"]
    )
    return (
        f"Hi,\n\n"
        f"Here's your weekly M4 Job Tracker summary:\n\n"
        f"Total active applications: {analytics['active_applications']}\n"
        f"New applications in the last 7 days: {analytics['applications_last_7_days']}\n"
        f"Interview rate: {analytics['interview_rate']}%\n"
        f"Offer rate: {analytics['offer_rate']}%\n"
        f"Applications going stale (14+ days, no update): {analytics['stale_applications']}\n\n"
        f"Status breakdown:\n{breakdown_lines}\n\n"
        f"Keep going — log in to review and follow up.\n"
    )


def _send_email(to_email: str, subject: str, body: str) -> bool:
    if not settings.SMTP_HOST or not settings.SMTP_USER:
        return False  # SMTP not configured; caller should treat as skipped, not failed

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM_EMAIL
    msg["To"] = to_email

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(settings.SMTP_FROM_EMAIL, [to_email], msg.as_string())
    return True


@router.post("/send-weekly")
def trigger_weekly_digest(x_digest_secret: str = Header(default="")):
    if x_digest_secret != settings.DIGEST_TRIGGER_SECRET:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid digest trigger secret")

    if not settings.SMTP_HOST:
        return {
            "sent": 0,
            "skipped": 0,
            "note": "SMTP not configured (SMTP_HOST empty) — digest sending is disabled. "
            "Set SMTP_HOST/SMTP_USER/SMTP_PASSWORD to enable.",
        }

    db: Session = SessionLocal()
    sent, failed = 0, 0
    try:
        users = db.query(User).all()
        for user in users:
            analytics = crud.get_analytics(db, user.id)
            if analytics["total_applications"] == 0:
                continue  # nothing to report, don't spam an empty digest
            body = _build_digest_body(user.email, analytics)
            try:
                if _send_email(user.email, "Your Weekly Job Search Digest", body):
                    sent += 1
            except (smtplib.SMTPException, OSError):
                failed += 1
    finally:
        db.close()

    return {"sent": sent, "failed": failed}
