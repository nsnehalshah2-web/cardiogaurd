from fastapi import APIRouter, Depends, HTTPException, Query
import json
import pickle
import pandas as pd
import shap
import os
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.assessment import AssessmentHistory
from app.models.user import User
from app.security import get_current_user
from app.schemas.assessment import ActionPlanItem, HealthDataInput, PredictionResponse

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, 'ml', 'model.pkl')
SCALER_PATH = os.path.join(BASE_DIR, 'ml', 'scaler.pkl')
METRICS_PATH = os.path.join(BASE_DIR, 'ml', 'metrics.json')
FEATURE_NAMES = ['age', 'sex', 'cp', 'trestbps', 'chol', 'fbs', 'restecg', 'thalach', 'exang', 'oldpeak']

try:
    with open(MODEL_PATH, 'rb') as f:
        model = pickle.load(f)
    with open(SCALER_PATH, 'rb') as f:
        scaler = pickle.load(f)
except Exception as e:
    print(f"Error loading model artifacts: {e}")


def build_action_plan(data: HealthDataInput | dict) -> list[ActionPlanItem]:
    values = data.model_dump() if isinstance(data, HealthDataInput) else data
    priorities = []
    trestbps = values.get('trestbps')
    if trestbps is not None and trestbps >= 130:
        priorities.append(ActionPlanItem(title="Focus on blood pressure", detail="Discuss repeated elevated readings with a qualified clinician."))
    chol = values.get('chol')
    if chol is not None and chol >= 200:
        priorities.append(ActionPlanItem(title="Review cholesterol", detail="Consider discussing your lipid results with a qualified clinician."))
    thalach = values.get('thalach')
    if thalach is not None and thalach < 120:
        priorities.append(ActionPlanItem(title="Discuss activity tolerance", detail="Ask a qualified clinician what level of physical activity is appropriate for you."))
    if values.get('cp') in (1, 2):
        priorities.append(ActionPlanItem(title="Talk about chest pain", detail="Describe when your chest discomfort happens to a qualified clinician."))
    if values.get('exang') == 1:
        priorities.append(ActionPlanItem(title="Mention exercise-related symptoms", detail="Discuss any symptoms during activity with a qualified clinician."))
    oldpeak = values.get('oldpeak')
    if oldpeak is not None and oldpeak >= 2:
        priorities.append(ActionPlanItem(title="Review exercise-test signals", detail="Discuss this exercise-related measure with a qualified clinician."))
    if values.get('fbs') == 1:
        priorities.append(ActionPlanItem(title="Review fasting sugar", detail="Consider discussing this fasting-sugar reading with a qualified clinician."))
    return priorities[:4]


def calculate_model_metrics() -> dict:
    # Written by ml/train_model.py from the held-out test split, which is never used for training.
    with open(METRICS_PATH) as f:
        return json.load(f)

@router.post("/predict", response_model=PredictionResponse)
def predict_risk(data: HealthDataInput, persist: bool = Query(True), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        # cp is None for assessments saved before chest pain type was added; XGBoost treats it as missing.
        input_data = pd.DataFrame([data.model_dump()], columns=FEATURE_NAMES).astype(float)
        input_scaled = scaler.transform(input_data)
        class_index = list(model.classes_).index(1)
        probability = float(model.predict_proba(input_scaled)[0][class_index] * 100)
        
        if probability < 33:
            category = "LOW"
        elif probability < 66:
            category = "MODERATE"
        else:
            category = "HIGH"
            
        explainer = shap.TreeExplainer(model)
        shap_vals = explainer.shap_values(input_scaled)
        
        shap_dict = {FEATURE_NAMES[i]: float(shap_vals[0][i]) for i in range(len(FEATURE_NAMES))}
        
        insights = []
        if data.trestbps > 130:
            insights.append("Your blood pressure is elevated. Consider monitoring it.")
        if data.chol > 200:
            insights.append("Cholesterol levels are above normal ranges.")
            
        if persist:
            assessment = AssessmentHistory(
                user_id=user.id,
                age=data.age,
                sex=data.sex,
                cp=data.cp,
                trestbps=data.trestbps,
                chol=data.chol,
                fbs=data.fbs,
                restecg=data.restecg,
                thalach=data.thalach,
                exang=data.exang,
                oldpeak=data.oldpeak,
                risk_probability=round(probability, 2),
                risk_category=category,
            )
            db.add(assessment)
            db.commit()

        return PredictionResponse(
            risk_probability=round(probability, 2),
            risk_category=category,
            shap_values=shap_dict,
            insights=insights,
            action_plan=build_action_plan(data),
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/model-insights")
def model_insights(user: User = Depends(get_current_user)):
    try:
        return calculate_model_metrics()
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Model evaluation is currently unavailable") from exc


@router.get("/history")
def assessment_history(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    records = db.query(AssessmentHistory).filter(AssessmentHistory.user_id == user.id).order_by(AssessmentHistory.created_at.desc()).all()
    return [
        {
            "id": record.id,
            "created_at": record.created_at,
            "risk_probability": record.risk_probability,
            "risk_category": record.risk_category,
            "form_data": {
                "age": record.age,
                "sex": record.sex,
                "cp": record.cp,
                "trestbps": record.trestbps,
                "chol": record.chol,
                "fbs": record.fbs,
                "restecg": record.restecg,
                "thalach": record.thalach,
                "exang": record.exang,
                "oldpeak": record.oldpeak,
            },
            "action_plan": [item.model_dump() for item in build_action_plan({
                "cp": record.cp,
                "trestbps": record.trestbps,
                "chol": record.chol,
                "thalach": record.thalach,
                "exang": record.exang,
                "oldpeak": record.oldpeak,
                "fbs": record.fbs,
            })],
        }
        for record in records
    ]