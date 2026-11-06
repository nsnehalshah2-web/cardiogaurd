"""Shared evaluation helpers: calibration and per-group (fairness) metrics."""
import numpy as np
from sklearn.calibration import calibration_curve
from sklearn.metrics import accuracy_score, brier_score_loss, recall_score, roc_auc_score


def calibration_report(y_true, probabilities, n_bins=8) -> dict:
    """How well predicted probabilities match observed rates (quantile bins so each has data)."""
    observed, predicted = calibration_curve(y_true, probabilities, n_bins=n_bins, strategy='quantile')
    return {
        'brier_score': round(float(brier_score_loss(y_true, probabilities)), 4),
        'bins': [
            {'predicted': round(float(p), 4), 'observed': round(float(o), 4)}
            for p, o in zip(predicted, observed)
        ],
    }


def group_report(groups, y_true, probabilities, threshold=0.5) -> list[dict]:
    """Accuracy, recall and ROC-AUC for each subgroup, e.g. women vs men."""
    groups = np.asarray(groups)
    y_true = np.asarray(y_true)
    probabilities = np.asarray(probabilities)
    rows = []
    for name in sorted(set(groups.tolist()), key=str):
        mask = groups == name
        y_group, p_group = y_true[mask], probabilities[mask]
        predictions = (p_group >= threshold).astype(int)
        rows.append({
            'group': str(name),
            'count': int(mask.sum()),
            'positive_rate': round(float(y_group.mean()), 4),
            'mean_predicted': round(float(p_group.mean()), 4),
            'accuracy': round(float(accuracy_score(y_group, predictions)), 4),
            'recall': round(float(recall_score(y_group, predictions, zero_division=0)), 4),
            # ROC-AUC needs both outcomes present in the group.
            'roc_auc': round(float(roc_auc_score(y_group, p_group)), 4) if len(set(y_group)) == 2 else None,
        })
    return rows


def age_band(age: float) -> str:
    if age < 50:
        return 'Under 50'
    if age < 60:
        return '50-59'
    return '60 and over'
