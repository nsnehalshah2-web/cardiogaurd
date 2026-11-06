from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from app.database.connection import Base


class HealthMeasurement(Base):
    __tablename__ = "health_measurements"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    measured_at = Column(DateTime(timezone=True), nullable=False, index=True)
    systolic_bp = Column(Integer)
    diastolic_bp = Column(Integer)
    weight_kg = Column(Float)
    heart_rate = Column(Integer)
    note = Column(String(300))


class VisitPreparation(Base):
    __tablename__ = "visit_preparations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    symptoms = Column(Text, nullable=False, default="")
    medications = Column(Text, nullable=False, default="")
    questions = Column(Text, nullable=False, default="")
    bring_medications = Column(Boolean, nullable=False, default=False)
    bring_test_results = Column(Boolean, nullable=False, default=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ReminderPreference(Base):
    __tablename__ = "reminder_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    email_enabled = Column(Boolean, nullable=False, default=False)


class HealthReminder(Base):
    __tablename__ = "health_reminders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    kind = Column(String(24), nullable=False)
    scheduled_at = Column(DateTime(timezone=True), nullable=False, index=True)
    note = Column(String(240))
    enabled = Column(Boolean, nullable=False, default=True)
    sent_at = Column(DateTime(timezone=True))
    attempt_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
