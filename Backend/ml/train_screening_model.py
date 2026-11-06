"""Train the home screening model on the Framingham Heart Study (4,240 people, 10-year follow-up).

It uses only things a person knows or can measure at home or at a pharmacy: no blood test,
ECG or treadmill test. Adding cholesterol or glucose did not improve cross-validated ROC-AUC
(0.727 either way), so the model leaves them out.

The model is logistic regression, so the whole model is a short list of numbers. They are
saved to screening_model.json, which both the API and the browser read; the browser copy lets
community health workers screen people with no internet connection.
"""
import json
import os

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from evaluation import age_band, calibration_report, group_report

ML_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(ML_DIR, 'framingham.csv')
OUTPUT_PATH = os.path.join(ML_DIR, 'screening_model.json')
# Parameters-only copy bundled into the frontend: powers the landing-page demo and lets
# screening work offline even before the app has fetched the model once.
FRONTEND_COPY = os.path.join(ML_DIR, '..', '..', 'Frontend', 'src', 'data', 'screening-model.json')
PARAMETER_FIELDS = ['features', 'medians', 'means', 'scales', 'coefficients', 'intercept', 'thresholds']
RANDOM_STATE = 42

# Framingham column -> API field name
FEATURES = {
    'age': 'age',
    'male': 'sex',
    'currentSmoker': 'smoker',
    'cigsPerDay': 'cigs_per_day',
    'BPMeds': 'bp_medication',
    'prevalentStroke': 'prior_stroke',
    'prevalentHyp': 'hypertension',
    'diabetes': 'diabetes',
    'sysBP': 'systolic_bp',
    'BMI': 'bmi',
}
# WHO risk-chart bands for 10-year cardiovascular risk.
THRESHOLDS = {'moderate': 0.10, 'high': 0.20}


def threshold_report(y_true, probabilities, threshold) -> dict:
    tn, fp, fn, tp = confusion_matrix(y_true, (probabilities >= threshold).astype(int), labels=[0, 1]).ravel()
    return {
        'threshold': threshold,
        'sensitivity': round(tp / (tp + fn), 4),
        'specificity': round(tn / (tn + fp), 4),
        'flagged_share': round((tp + fp) / len(y_true), 4),
        'confusion_matrix': [[int(tn), int(fp)], [int(fn), int(tp)]],
    }


def train():
    if not os.path.exists(DATA_PATH):
        print(f"'{DATA_PATH}' not found. Run `python prepare_framingham.py` first.")
        return

    df = pd.read_csv(DATA_PATH)
    X = df[list(FEATURES)].rename(columns=FEATURES)
    y = df['TenYearCHD']

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=RANDOM_STATE
    )
    pipeline = make_pipeline(
        SimpleImputer(strategy='median'), StandardScaler(), LogisticRegression(max_iter=1000)
    )
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    cv_auc = cross_val_score(pipeline, X_train, y_train, cv=cv, scoring='roc_auc')
    pipeline.fit(X_train, y_train)

    probabilities = pipeline.predict_proba(X_test)[:, 1]
    test_auc = roc_auc_score(y_test, probabilities)
    imputer, scaler, model = pipeline.named_steps.values()

    sexes = np.where(X_test['sex'] == 1, 'Men', 'Women')
    ages = X_test['age'].map(age_band).to_numpy()
    report = {
        'name': 'CardioGuard home screening model',
        'outcome': 'Coronary heart disease within 10 years',
        'dataset': f'Framingham Heart Study teaching dataset: {len(df)} participants, '
                   f'{int(y.sum())} developed coronary heart disease within 10 years',
        'evaluation_method': 'Stratified held-out test split (20%, never used for training); '
                             f'5-fold cross-validation ROC-AUC on the training set: '
                             f'{cv_auc.mean():.3f} ± {cv_auc.std():.3f}',
        'train_count': int(len(y_train)),
        'sample_count': int(len(y_test)),
        'features': list(FEATURES.values()),
        'medians': [round(float(v), 6) for v in imputer.statistics_],
        'means': [round(float(v), 6) for v in scaler.mean_],
        'scales': [round(float(v), 6) for v in scaler.scale_],
        'coefficients': [round(float(v), 6) for v in model.coef_[0]],
        'intercept': round(float(model.intercept_[0]), 6),
        'thresholds': THRESHOLDS,
        'metrics': {
            'roc_auc': round(float(test_auc), 4),
            'cv_roc_auc_mean': round(float(cv_auc.mean()), 4),
            'cv_roc_auc_std': round(float(cv_auc.std()), 4),
            'base_rate': round(float(y.mean()), 4),
        },
        'operating_points': [threshold_report(y_test.to_numpy(), probabilities, t) for t in THRESHOLDS.values()],
        'calibration': calibration_report(y_test, probabilities),
        'fairness': {
            'threshold': THRESHOLDS['moderate'],
            'by_sex': group_report(sexes, y_test, probabilities, THRESHOLDS['moderate']),
            'by_age': group_report(ages, y_test, probabilities, THRESHOLDS['moderate']),
        },
    }

    with open(OUTPUT_PATH, 'w') as f:
        json.dump(report, f, indent=2)
    os.makedirs(os.path.dirname(FRONTEND_COPY), exist_ok=True)
    with open(FRONTEND_COPY, 'w') as f:
        json.dump({key: report[key] for key in PARAMETER_FIELDS}, f, indent=2)

    print(report['dataset'])
    print(f"5-fold CV ROC-AUC: {cv_auc.mean():.3f} ± {cv_auc.std():.3f}   held-out ROC-AUC: {test_auc:.3f}")
    print(f"Brier score: {report['calibration']['brier_score']}")
    for point in report['operating_points']:
        print(f"  refer at >= {point['threshold']:.0%}: sensitivity {point['sensitivity']:.1%}, "
              f"specificity {point['specificity']:.1%}, flags {point['flagged_share']:.1%} of people")
    for row in report['fairness']['by_sex'] + report['fairness']['by_age']:
        print(f"  {row['group']:12s} n={row['count']:4d} AUC={row['roc_auc']} recall={row['recall']}")
    for name, coef in zip(report['features'], report['coefficients']):
        print(f"  {name:14s} {coef:+.3f}")
    print(f"Saved {OUTPUT_PATH}")


if __name__ == "__main__":
    train()
