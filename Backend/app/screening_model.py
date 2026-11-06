"""Home screening model: logistic regression read from ml/screening_model.json.

The browser runs the same calculation from the same file (Frontend/src/services/screeningModel.js)
so community health workers can screen offline; keep the two in step.
"""
import json
import math
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
MODEL_PATH = os.path.join(BASE_DIR, 'ml', 'screening_model.json')

with open(MODEL_PATH) as f:
    MODEL = json.load(f)

FEATURE_LABELS = {
    'age': 'Age',
    'sex': 'Sex',
    'smoker': 'Smoking',
    'cigs_per_day': 'Cigarettes per day',
    'bp_medication': 'Blood pressure medicine',
    'prior_stroke': 'Previous stroke',
    'hypertension': 'Diagnosed high blood pressure',
    'diabetes': 'Diabetes',
    'systolic_bp': 'Systolic blood pressure',
    'bmi': 'Body mass index',
}


def category_for(probability: float) -> str:
    if probability >= MODEL['thresholds']['high']:
        return 'HIGH'
    if probability >= MODEL['thresholds']['moderate']:
        return 'MODERATE'
    return 'LOW'


def predict(values: dict) -> dict:
    """values maps feature name -> number or None (None = unknown, filled with the training median)."""
    contributions = {}
    logit = MODEL['intercept']
    for name, median, mean, scale, coef in zip(
        MODEL['features'], MODEL['medians'], MODEL['means'], MODEL['scales'], MODEL['coefficients']
    ):
        value = values.get(name)
        value = median if value is None else float(value)
        contribution = coef * (value - mean) / scale
        contributions[name] = round(contribution, 4)
        logit += contribution
    probability = 1 / (1 + math.exp(-logit))
    return {
        'risk_probability': round(probability * 100, 2),
        'risk_category': category_for(probability),
        'contributions': contributions,
    }


def recommendations(values: dict, category: str) -> list[dict]:
    items = []
    if category == 'HIGH':
        items.append({'title': 'See a doctor soon', 'detail': 'Visit a doctor or the nearest health centre within the next few weeks for a full heart check.'})
    elif category == 'MODERATE':
        items.append({'title': 'Plan a check-up', 'detail': 'Get your blood pressure, blood sugar and cholesterol checked at a health centre in the next few months.'})
    if values.get('smoker'):
        items.append({'title': 'Stop smoking', 'detail': 'Stopping smoking is the single biggest change you can make. Ask a health worker about free quit support.'})
    systolic = values.get('systolic_bp')
    if systolic is not None and systolic >= 140:
        items.append({'title': 'Blood pressure is high', 'detail': 'A reading of 140 or more needs to be confirmed and treated. Recheck it on another day.'})
    elif systolic is not None and systolic >= 130:
        items.append({'title': 'Watch your blood pressure', 'detail': 'Reduce salt, stay active, and check your blood pressure every few months.'})
    bmi = values.get('bmi')
    # Asian BMI cut-off for overweight is 23 (WHO expert consultation, 2004).
    if bmi is not None and bmi >= 23:
        items.append({'title': 'Aim for a healthy weight', 'detail': 'A BMI of 23 or more is overweight for South Asian adults. Regular walking and less fried food help.'})
    if values.get('diabetes'):
        items.append({'title': 'Keep blood sugar controlled', 'detail': 'Take diabetes medicine as prescribed and check your sugar regularly.'})
    if not items:
        items.append({'title': 'Keep it up', 'detail': 'Stay active, eat less salt and oil, avoid tobacco, and repeat this check every year.'})
    return items[:4]
