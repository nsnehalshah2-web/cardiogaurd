from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_serializer, model_validator


def _require_timezone(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("A timezone is required")
    return value.astimezone(timezone.utc)


class HealthMeasurementCreate(BaseModel):
    measured_at: datetime
    systolic_bp: int | None = Field(None, ge=50, le=300)
    diastolic_bp: int | None = Field(None, ge=30, le=200)
    weight_kg: float | None = Field(None, ge=1, le=500)
    heart_rate: int | None = Field(None, ge=20, le=250)
    note: str | None = Field(None, max_length=300)

    @model_validator(mode="after")
    def validate_measurement(self):
        self.measured_at = _require_timezone(self.measured_at)
        if (self.systolic_bp is None) != (self.diastolic_bp is None):
            raise ValueError("Enter both systolic and diastolic blood pressure")
        if all(value is None for value in (self.systolic_bp, self.weight_kg, self.heart_rate)):
            raise ValueError("Enter at least one measurement")
        return self


class HealthMeasurementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    measured_at: datetime
    systolic_bp: int | None
    diastolic_bp: int | None
    weight_kg: float | None
    heart_rate: int | None
    note: str | None

    @field_serializer("measured_at")
    def serialize_measured_at(self, value: datetime) -> datetime:
        return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


class VisitPreparationData(BaseModel):
    symptoms: str = Field("", max_length=4000)
    medications: str = Field("", max_length=4000)
    questions: str = Field("", max_length=4000)
    bring_medications: bool = False
    bring_test_results: bool = False


class VisitPreparationResponse(VisitPreparationData):
    updated_at: datetime | None = None


class ReminderCreate(BaseModel):
    kind: Literal["screening", "referral"]
    scheduled_at: datetime
    note: str | None = Field(None, max_length=240)

    @model_validator(mode="after")
    def validate_schedule(self):
        self.scheduled_at = _require_timezone(self.scheduled_at)
        if self.scheduled_at <= datetime.now(timezone.utc):
            raise ValueError("Choose a reminder time in the future")
        return self


class ReminderUpdate(BaseModel):
    enabled: bool


class ReminderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    kind: str
    scheduled_at: datetime
    note: str | None
    enabled: bool
    sent_at: datetime | None
    attempt_count: int

    @field_serializer("scheduled_at", "sent_at")
    def serialize_reminder_times(self, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


class ReminderPreferenceUpdate(BaseModel):
    email_enabled: bool


class ReminderPreferenceResponse(BaseModel):
    email_enabled: bool
    email_configured: bool
