from typing import Optional

from pydantic import BaseModel, Field


class ActionPlanItem(BaseModel):
    title: str
    detail: str

class HealthDataInput(BaseModel):
    age: int = Field(..., ge=1, le=120)
    sex: int = Field(..., description="0 for female, 1 for male")
    cp: Optional[int] = Field(None, ge=1, le=4, description="Chest pain type (1 typical angina, 2 atypical angina, 3 non-anginal pain, 4 no chest pain)")
    trestbps: int = Field(..., description="Resting blood pressure")
    chol: int = Field(..., description="Serum cholesterol in mg/dl")
    fbs: int = Field(..., description="Fasting blood sugar > 120 mg/dl (1 = true; 0 = false)")
    restecg: int = Field(..., description="Resting electrocardiographic results (0, 1, 2)")
    thalach: int = Field(..., description="Maximum heart rate achieved")
    exang: int = Field(..., description="Exercise induced angina (1 = yes; 0 = no)")
    oldpeak: float = Field(..., description="ST depression induced by exercise relative to rest")

class PredictionResponse(BaseModel):
    risk_probability: float
    risk_category: str
    shap_values: dict
    insights: list
    action_plan: list[ActionPlanItem]