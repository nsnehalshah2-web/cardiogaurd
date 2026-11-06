import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import screening_model
from app.database.connection import get_db
from app.models.community import Patient, Screening
from app.models.user import User
from app.schemas.screening import ReferralUpdate, ScreeningInput, ScreeningResult, SyncRequest
from app.security import get_current_user

router = APIRouter()

INPUT_FIELDS = list(ScreeningInput.model_fields)
MODEL_FIELDS = ['features', 'medians', 'means', 'scales', 'coefficients', 'intercept', 'thresholds']


def screening_values(data: ScreeningInput) -> dict:
    values = data.model_dump(include=set(INPUT_FIELDS))
    if not values['smoker']:
        values['cigs_per_day'] = 0
    return values


def serialize_screening(record: Screening) -> dict:
    values = {name: getattr(record, name) for name in INPUT_FIELDS}
    return {
        'id': record.id,
        'client_id': record.client_id,
        'patient_id': record.patient_id,
        'screened_at': record.screened_at,
        'risk_probability': record.risk_probability,
        'risk_category': record.risk_category,
        'referral_status': record.referral_status,
        'form_data': values,
        'recommendations': screening_model.recommendations(values, record.risk_category),
    }


def serialize_patient(patient: Patient, include_screenings: bool = False) -> dict:
    latest = patient.screenings[0] if patient.screenings else None
    data = {
        'id': patient.id,
        'client_id': patient.client_id,
        'name': patient.name,
        'age': patient.age,
        'sex': patient.sex,
        'village': patient.village,
        'phone': patient.phone,
        'created_at': patient.created_at,
        'screening_count': len(patient.screenings),
        'latest': serialize_screening(latest) if latest else None,
    }
    if include_screenings:
        data['screenings'] = [serialize_screening(item) for item in patient.screenings]
    return data


@router.get("/screening/model")
def public_screening_model():
    """Model parameters for running the screening in the browser while offline."""
    return {key: screening_model.MODEL[key] for key in MODEL_FIELDS}


@router.get("/screening/model-insights")
def screening_model_insights(user: User = Depends(get_current_user)):
    return screening_model.MODEL


@router.post("/screening/predict", response_model=ScreeningResult)
def screen_self(data: ScreeningInput, persist: bool = Query(True), user: User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    values = screening_values(data)
    result = screening_model.predict(values)
    if persist:
        db.add(Screening(owner_id=user.id, client_id=uuid.uuid4().hex, risk_probability=result['risk_probability'],
                         risk_category=result['risk_category'], **values))
        db.commit()
    return {**result, 'recommendations': screening_model.recommendations(values, result['risk_category'])}


@router.get("/screening/history")
def self_screening_history(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    records = (db.query(Screening)
               .filter(Screening.owner_id == user.id, Screening.patient_id.is_(None))
               .order_by(Screening.screened_at.desc()).all())
    return [serialize_screening(record) for record in records]


@router.post("/community/sync")
def sync_community(data: SyncRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Save patients and screenings recorded in the browser (possibly offline).

    Records are keyed by the browser-generated client_id, so sending the same batch twice
    (e.g. after a dropped connection) doesn't create duplicates. Risk is recalculated here.
    """
    rejected = []
    for item in data.patients:
        patient = db.query(Patient).filter(Patient.client_id == item.client_id).first()
        if patient and patient.owner_id != user.id:
            rejected.append(item.client_id)
            continue
        fields = item.model_dump(exclude={'client_id'})
        if patient:
            for key, value in fields.items():
                setattr(patient, key, value)
        else:
            db.add(Patient(owner_id=user.id, client_id=item.client_id, **fields))
    db.flush()

    for item in data.screenings:
        if db.query(Screening).filter(Screening.client_id == item.client_id).first():
            continue
        patient_id = None
        if item.patient_client_id:
            patient = db.query(Patient).filter(Patient.client_id == item.patient_client_id,
                                               Patient.owner_id == user.id).first()
            if not patient:
                rejected.append(item.client_id)
                continue
            patient_id = patient.id
        values = screening_values(item)
        result = screening_model.predict(values)
        record = Screening(owner_id=user.id, patient_id=patient_id, client_id=item.client_id,
                           risk_probability=result['risk_probability'], risk_category=result['risk_category'],
                           **values)
        if item.screened_at:
            record.screened_at = item.screened_at
        db.add(record)
    db.commit()
    return {'rejected': rejected}


@router.get("/community/patients")
def list_patients(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    patients = db.query(Patient).filter(Patient.owner_id == user.id).order_by(Patient.created_at.desc()).all()
    return [serialize_patient(patient) for patient in patients]


@router.get("/community/patients/{patient_id}")
def get_patient(patient_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == patient_id, Patient.owner_id == user.id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return serialize_patient(patient, include_screenings=True)


@router.patch("/community/screenings/{screening_id}")
def update_referral(screening_id: int, data: ReferralUpdate, user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    record = db.query(Screening).filter(Screening.id == screening_id, Screening.owner_id == user.id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Screening not found")
    record.referral_status = data.referral_status
    db.commit()
    return serialize_screening(record)
