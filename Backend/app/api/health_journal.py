import hmac
import os
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.health_journal import HealthMeasurement, HealthReminder, ReminderPreference, VisitPreparation
from app.models.user import User
from app.schemas.health_journal import (
    HealthMeasurementCreate,
    HealthMeasurementResponse,
    ReminderCreate,
    ReminderPreferenceResponse,
    ReminderPreferenceUpdate,
    ReminderResponse,
    ReminderUpdate,
    VisitPreparationData,
    VisitPreparationResponse,
)
from app.security import get_current_user

router = APIRouter()


def _email_configured() -> bool:
    return bool(os.getenv("RESEND_API_KEY") and os.getenv("RESEND_FROM_EMAIL"))


def _get_preference(db: Session, user_id: int) -> ReminderPreference:
    preference = db.query(ReminderPreference).filter(ReminderPreference.user_id == user_id).first()
    if preference is None:
        preference = ReminderPreference(user_id=user_id, email_enabled=False)
        db.add(preference)
        db.commit()
        db.refresh(preference)
    return preference


@router.get("/measurements", response_model=list[HealthMeasurementResponse])
def list_measurements(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(HealthMeasurement)
        .filter(HealthMeasurement.user_id == user.id)
        .order_by(HealthMeasurement.measured_at.desc(), HealthMeasurement.id.desc())
        .limit(500)
        .all()
    )


@router.post("/measurements", response_model=HealthMeasurementResponse, status_code=status.HTTP_201_CREATED)
def create_measurement(
    data: HealthMeasurementCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    measurement = HealthMeasurement(user_id=user.id, **data.model_dump())
    db.add(measurement)
    db.commit()
    db.refresh(measurement)
    return measurement


@router.delete("/measurements/{measurement_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_measurement(
    measurement_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    measurement = db.query(HealthMeasurement).filter(
        HealthMeasurement.id == measurement_id,
        HealthMeasurement.user_id == user.id,
    ).first()
    if measurement is None:
        raise HTTPException(status_code=404, detail="Measurement not found")
    db.delete(measurement)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/visit-preparation", response_model=VisitPreparationResponse)
def get_visit_preparation(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    preparation = db.query(VisitPreparation).filter(VisitPreparation.user_id == user.id).first()
    return preparation or VisitPreparationResponse()


@router.put("/visit-preparation", response_model=VisitPreparationResponse)
def save_visit_preparation(
    data: VisitPreparationData,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    preparation = db.query(VisitPreparation).filter(VisitPreparation.user_id == user.id).first()
    if preparation is None:
        preparation = VisitPreparation(user_id=user.id)
        db.add(preparation)
    for key, value in data.model_dump().items():
        setattr(preparation, key, value)
    db.commit()
    db.refresh(preparation)
    return preparation


@router.get("/reminder-preferences", response_model=ReminderPreferenceResponse)
def get_reminder_preferences(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    preference = _get_preference(db, user.id)
    return ReminderPreferenceResponse(
        email_enabled=preference.email_enabled,
        email_configured=_email_configured(),
    )


@router.put("/reminder-preferences", response_model=ReminderPreferenceResponse)
def update_reminder_preferences(
    data: ReminderPreferenceUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if data.email_enabled and not _email_configured():
        raise HTTPException(status_code=503, detail="Email reminders are not configured yet")
    preference = _get_preference(db, user.id)
    preference.email_enabled = data.email_enabled
    if not data.email_enabled:
        db.query(HealthReminder).filter(
            HealthReminder.user_id == user.id,
            HealthReminder.enabled.is_(True),
            HealthReminder.sent_at.is_(None),
        ).update({HealthReminder.enabled: False}, synchronize_session=False)
    db.commit()
    return ReminderPreferenceResponse(
        email_enabled=preference.email_enabled,
        email_configured=_email_configured(),
    )


@router.get("/reminders", response_model=list[ReminderResponse])
def list_reminders(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(HealthReminder)
        .filter(HealthReminder.user_id == user.id)
        .order_by(HealthReminder.scheduled_at.desc(), HealthReminder.id.desc())
        .limit(200)
        .all()
    )


@router.post("/reminders", response_model=ReminderResponse, status_code=status.HTTP_201_CREATED)
def create_reminder(
    data: ReminderCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    preference = _get_preference(db, user.id)
    if not preference.email_enabled:
        raise HTTPException(status_code=409, detail="Enable email reminders in Settings first")
    if not _email_configured():
        raise HTTPException(status_code=503, detail="Email reminders are not configured yet")
    reminder = HealthReminder(user_id=user.id, **data.model_dump())
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    return reminder


@router.patch("/reminders/{reminder_id}", response_model=ReminderResponse)
def update_reminder(
    reminder_id: int,
    data: ReminderUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    reminder = db.query(HealthReminder).filter(
        HealthReminder.id == reminder_id,
        HealthReminder.user_id == user.id,
        HealthReminder.sent_at.is_(None),
    ).first()
    if reminder is None:
        raise HTTPException(status_code=404, detail="Upcoming reminder not found")
    reminder.enabled = data.enabled
    db.commit()
    db.refresh(reminder)
    return reminder


def send_reminder_email(email: str, kind: str, frontend_url: str, reminder_id: int) -> None:
    api_key = os.getenv("RESEND_API_KEY")
    from_email = os.getenv("RESEND_FROM_EMAIL")
    if not api_key or not from_email:
        raise RuntimeError("Email reminders are not configured")
    activity = "repeat your screening" if kind == "screening" else "follow up on your referral"
    payload = {
        "from": from_email,
        "to": [email],
        "subject": "Your CardioGuard reminder",
        "text": (
            f"You asked CardioGuard to remind you to {activity}.\n\n"
            "Sign in to view your health journal and reminder details:\n"
            f"{frontend_url.rstrip('/')}/#/health-journal\n\n"
            "This reminder is not medical advice. For urgent symptoms, contact local emergency services."
        ),
    }
    timeout = httpx.Timeout(connect=5.0, read=10.0, write=10.0, pool=5.0)
    response = httpx.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {api_key}", "Idempotency-Key": f"cardioguard-reminder-{reminder_id}"},
        json=payload,
        timeout=timeout,
    )
    response.raise_for_status()


@router.post("/reminders/dispatch")
def dispatch_due_reminders(
    authorization: str | None = Header(None),
    db: Session = Depends(get_db),
):
    expected_token = os.getenv("REMINDER_JOB_TOKEN")
    if not expected_token:
        raise HTTPException(status_code=503, detail="Reminder dispatcher is not configured")
    supplied_token = authorization.removeprefix("Bearer ").strip() if authorization else ""
    if not supplied_token or not hmac.compare_digest(supplied_token.encode("utf-8"), expected_token.encode("utf-8")):
        raise HTTPException(status_code=401, detail="Unauthorized")
    if not _email_configured():
        raise HTTPException(status_code=503, detail="Email reminders are not configured")

    due = (
        db.query(HealthReminder, User)
        .join(User, User.id == HealthReminder.user_id)
        .join(ReminderPreference, ReminderPreference.user_id == User.id)
        .filter(
            HealthReminder.enabled.is_(True),
            HealthReminder.sent_at.is_(None),
            HealthReminder.scheduled_at <= datetime.now(timezone.utc),
            ReminderPreference.email_enabled.is_(True),
        )
        .order_by(HealthReminder.scheduled_at.asc(), HealthReminder.id.asc())
        .limit(100)
        .all()
    )
    frontend_url = os.getenv("FRONTEND_URL", "https://nsnehalshah2-web.github.io/cardiogaurd/")
    sent = 0
    failed = []
    for reminder, user in due:
        reminder.attempt_count += 1
        try:
            send_reminder_email(user.email, reminder.kind, frontend_url, reminder.id)
        except (httpx.HTTPError, RuntimeError):
            failed.append(reminder.id)
        else:
            reminder.sent_at = datetime.now(timezone.utc)
            reminder.enabled = False
            sent += 1
        db.commit()
    if failed:
        raise HTTPException(
            status_code=502,
            detail={"message": "Some due reminders could not be sent and will be retried", "failed_count": len(failed)},
        )
    return {"sent": sent}
