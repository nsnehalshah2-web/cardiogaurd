import hmac
import os

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.assessment import AssessmentHistory
from app.models.community import Patient, Screening
from app.models.health_journal import HealthMeasurement, HealthReminder, ReminderPreference, VisitPreparation
from app.models.password_reset import PasswordResetToken
from app.models.user import User

router = APIRouter()


@router.post("/purge-all-accounts")
def purge_all_accounts(
    authorization: str | None = Header(None),
    db: Session = Depends(get_db),
):
    expected_token = os.getenv("ONE_TIME_ACCOUNT_PURGE_TOKEN")
    supplied_token = authorization.removeprefix("Bearer ").strip() if authorization else ""
    if not expected_token:
        raise HTTPException(status_code=404, detail="Not found")
    if not supplied_token or not hmac.compare_digest(supplied_token, expected_token):
        raise HTTPException(status_code=401, detail="Unauthorized")

    deleted_users = db.query(User).count()
    db.query(Screening).delete(synchronize_session=False)
    db.query(Patient).delete(synchronize_session=False)
    db.query(AssessmentHistory).delete(synchronize_session=False)
    db.query(PasswordResetToken).delete(synchronize_session=False)
    db.query(HealthMeasurement).delete(synchronize_session=False)
    db.query(HealthReminder).delete(synchronize_session=False)
    db.query(ReminderPreference).delete(synchronize_session=False)
    db.query(VisitPreparation).delete(synchronize_session=False)
    db.query(User).delete(synchronize_session=False)
    db.commit()
    return {"deleted_accounts": deleted_users}
