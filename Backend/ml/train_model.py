"""Train the CardioGuard model on the real UCI Heart Disease database (920 patients, 4 hospitals).

Why the old numbers were wrong: heart.csv / heart_2.csv contain 1025 rows but only 302 unique
patients (the rest are copies), so most "test" rows were also in the training set and the
reported ~97% accuracy was memorisation. This script de-duplicates, keeps a stratified held-out
test set the model never sees, and reports 5-fold cross-validation on the training data.
"""
import json
import os
import pickle

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import (accuracy_score, classification_report, confusion_matrix, f1_score,
                             precision_score, recall_score, roc_auc_score)
from sklearn.model_selection import GridSearchCV, StratifiedKFold, cross_val_score, train_test_split
from sklearn.preprocessing import StandardScaler

from evaluation import age_band, calibration_report, group_report

ML_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(ML_DIR, 'heart_disease_uci.csv')
FEATURE_NAMES = ['age', 'sex', 'cp', 'trestbps', 'chol', 'fbs', 'restecg', 'thalach', 'exang', 'oldpeak']
RANDOM_STATE = 42


def train_and_save_model():
    if not os.path.exists(DATA_PATH):
        print(f"'{DATA_PATH}' not found. Run `python prepare_dataset.py` first.")
        return

    df = pd.read_csv(DATA_PATH).drop_duplicates(subset=FEATURE_NAMES + ['target'])
    X = df[FEATURE_NAMES]
    y = df['target']

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=RANDOM_STATE
    )
    test_sources = df.loc[X_test.index, 'source'].to_numpy()

    # Trees don't need scaling, but the API applies scaler.pkl before the model, so keep the
    # same pipeline. StandardScaler ignores NaN when fitting and passes it through; XGBoost
    # learns its own direction for missing values (e.g. the unmeasured Swiss cholesterol).
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    search = GridSearchCV(
        xgb.XGBClassifier(objective='binary:logistic', eval_metric='logloss', subsample=0.8,
                          colsample_bytree=0.8, random_state=RANDOM_STATE),
        param_grid={
            'max_depth': [2, 3, 4],
            'learning_rate': [0.02, 0.05],
            'n_estimators': [200, 400],
            'min_child_weight': [1, 3],
        },
        scoring='roc_auc',
        cv=cv,
    )
    search.fit(X_train_scaled, y_train)
    model = search.best_estimator_
    cv_accuracy = cross_val_score(model, X_train_scaled, y_train, cv=cv, scoring='accuracy')

    predictions = model.predict(X_test_scaled)
    probabilities = model.predict_proba(X_test_scaled)[:, list(model.classes_).index(1)]
    metrics = {
        'accuracy': accuracy_score(y_test, predictions),
        'precision': precision_score(y_test, predictions, zero_division=0),
        'recall': recall_score(y_test, predictions, zero_division=0),
        'f1_score': f1_score(y_test, predictions, zero_division=0),
        'roc_auc': roc_auc_score(y_test, probabilities),
    }

    print(f"Dataset: {len(df)} unique patients ({int(y.sum())} with heart disease)")
    print("Best parameters:", search.best_params_)
    print(f"5-fold CV accuracy (train set): {cv_accuracy.mean():.3f} ± {cv_accuracy.std():.3f}")
    print(f"Held-out test accuracy: {metrics['accuracy']:.3f}   ROC-AUC: {metrics['roc_auc']:.3f}")
    print(classification_report(y_test, predictions))

    importance = sorted(
        ({'feature': name, 'importance': round(float(value), 6)}
         for name, value in zip(FEATURE_NAMES, model.feature_importances_)),
        key=lambda item: item['importance'], reverse=True,
    )
    report = {
        'evaluation_method': 'Stratified held-out test split (20%, never used for training or tuning); '
                             f'5-fold cross-validation accuracy on the training set: '
                             f'{cv_accuracy.mean():.1%} ± {cv_accuracy.std():.1%}',
        'dataset': f'UCI Heart Disease database: {len(df)} real patients from Cleveland, Hungary, '
                   'Switzerland and VA Long Beach',
        'sample_count': int(len(y_test)),
        'train_count': int(len(y_train)),
        'cv_accuracy_mean': round(float(cv_accuracy.mean()), 4),
        'cv_accuracy_std': round(float(cv_accuracy.std()), 4),
        'best_params': search.best_params_,
        'metrics': {key: round(float(value), 4) for key, value in metrics.items()},
        'confusion_matrix': confusion_matrix(y_test, predictions, labels=[0, 1]).tolist(),
        'confusion_matrix_labels': ['No detected disease', 'Detected disease'],
        'feature_importance': importance,
        'calibration': calibration_report(y_test, probabilities),
        'fairness': {
            'threshold': 0.5,
            'by_sex': group_report(np.where(X_test['sex'] == 1, 'Men', 'Women'), y_test, probabilities),
            'by_age': group_report(X_test['age'].map(age_band).to_numpy(), y_test, probabilities),
            'by_hospital': group_report(test_sources, y_test, probabilities),
        },
    }

    with open(os.path.join(ML_DIR, 'model.pkl'), 'wb') as f:
        pickle.dump(model, f)
    with open(os.path.join(ML_DIR, 'scaler.pkl'), 'wb') as f:
        pickle.dump(scaler, f)
    with open(os.path.join(ML_DIR, 'metrics.json'), 'w') as f:
        json.dump(report, f, indent=2)

    for row in report['fairness']['by_sex'] + report['fairness']['by_age'] + report['fairness']['by_hospital']:
        print(f"  {row['group']:14s} n={row['count']:4d} accuracy={row['accuracy']} AUC={row['roc_auc']}")
    print(f"Brier score: {report['calibration']['brier_score']}")
    print("Saved model.pkl, scaler.pkl and metrics.json.")


if __name__ == "__main__":
    train_and_save_model()
