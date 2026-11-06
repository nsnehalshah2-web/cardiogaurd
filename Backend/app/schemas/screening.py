from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class ScreeningInput(BaseModel):
    age: int = Field(..., ge=18, le=100)
    sex: int = Field(..., ge=0, le=1, description="0 female, 1 male")
    smoker: int = Field(..., ge=0, le=1)
    cigs_per_day: int = Field(0, ge=0, le=100)
    bp_medication: int = Field(0, ge=0, le=1)
    prior_stroke: int = Field(0, ge=0, le=1)
    hypertension: int = Field(0, ge=0, le=1, description="Ever told by a doctor you have high blood pressure")
    diabetes: int = Field(0, ge=0, le=1)
    systolic_bp: float = Field(..., ge=70, le=260, description="Upper blood pressure number, mmHg")
    bmi: Optional[float] = Field(None, ge=12, le=70, description="Leave empty if height/weight unknown")


class ScreeningResult(BaseModel):
    risk_probability: float
    risk_category: str
    contributions: dict
    recommendations: list[dict]


class PatientIn(BaseModel):
    client_id: str = Field(..., min_length=8, max_length=64)
    name: str = Field(..., min_length=1, max_length=120)
    age: Optional[int] = Field(None, ge=1, le=120)
    sex: Optional[int] = Field(None, ge=0, le=1)
    village: Optional[str] = Field(None, max_length=120)
    phone: Optional[str] = Field(None, max_length=30)


class ScreeningIn(ScreeningInput):
    client_id: str = Field(..., min_length=8, max_length=64)
    patient_client_id: Optional[str] = Field(None, max_length=64)
    screened_at: Optional[datetime] = None


class SyncRequest(BaseModel):
    patients: list[PatientIn] = Field(default_factory=list, max_length=500)
    screenings: list[ScreeningIn] = Field(default_factory=list, max_length=1000)


class ReferralUpdate(BaseModel):
    referral_status: Literal['none', 'referred', 'visited']
