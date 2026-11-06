# CardioGuard model card

CardioGuard has two models. Both are screening estimates, not diagnoses. All numbers below come from held-out test sets that were never used for training or tuning, and are reproduced by the training scripts in `Backend/ml/`.

## 1. Home screening model

| | |
|---|---|
| **Purpose** | 10-year risk of coronary heart disease from questions anyone can answer plus a blood pressure reading. Built for self-checks and community health workers (ASHA). |
| **Not for** | People who already have heart disease, or anyone with symptoms right now (the app sends them to the emergency check first). |
| **Algorithm** | Logistic regression (median imputation, standard scaling). Exported to `screening_model.json` so it also runs in the browser offline. |
| **Inputs** | Age, sex, smoking, cigarettes per day, BP medicine, previous stroke, diagnosed hypertension, diabetes, systolic BP, BMI (optional). |
| **Training data** | Framingham Heart Study teaching dataset: 4,240 adults aged 32–70, Framingham, USA; 644 (15.2%) developed CHD within 10 years. |
| **Script** | `python prepare_framingham.py && python train_screening_model.py` |

**Results (848 held-out people)**

| Metric | Value |
|---|---|
| ROC-AUC (held-out) | 0.705 |
| ROC-AUC (5-fold CV on training set) | 0.732 ± 0.033 |
| Brier score | 0.122 |
| At ≥ 10% ("moderate"): sensitivity / specificity | 79.8% / 50.5% |
| At ≥ 20% ("high", refer): sensitivity / specificity | 45.7% / 79.5% |

Accuracy is not reported: only 15% of people develop CHD, so predicting "no" for everyone would score 85%.

**Design decision:** adding total cholesterol and glucose did not change cross-validated ROC-AUC (0.727 with or without), so the model doesn't ask for any blood test.

**Fairness (held-out set):** ROC-AUC is 0.69 for both men and women. By age: 0.72 under 50, 0.65 for 50–59 and 0.65 for 60+. Discrimination is weaker within older groups because age itself is the strongest predictor.

**Limitations**
- Framingham participants were mostly white Americans recruited from 1948 onwards. South Asians develop heart disease earlier and at lower BMI, so the model may **underestimate** risk for Indian users. The app says this on every result.
- Risk bands follow the WHO risk-chart cut-offs (10% and 20%), but the model has not been validated on an Indian population.

## 2. Clinical model

| | |
|---|---|
| **Purpose** | Probability of significant coronary artery disease (> 50% narrowing on angiography) for someone with clinical test results. |
| **Not for** | Diagnosis or emergencies; people without ECG/exercise-test results (use home screening). |
| **Algorithm** | XGBoost, tuned with 5-fold grid search on the training set only. |
| **Inputs** | Age, sex, chest pain type, resting BP, cholesterol, fasting blood sugar > 120, resting ECG, max heart rate, exercise angina, ST depression. |
| **Training data** | UCI Heart Disease database: 918 unique patients from Cleveland, Hungary, Switzerland and VA Long Beach; 508 (55%) had disease. |
| **Script** | `python prepare_dataset.py && python train_model.py` |

**Results (184 held-out patients)**

| Metric | Value |
|---|---|
| Accuracy | 82.1% |
| Precision | 83.5% |
| Recall | 84.3% |
| F1 | 83.9% |
| ROC-AUC | 0.915 |
| Brier score | 0.117 |
| 5-fold CV accuracy (training set) | 81.2% ± 3.5% |

**Fairness (held-out set):** men 80.5% accuracy (ROC-AUC 0.90, n = 149); women 88.6% (ROC-AUC 0.91, n = 35). By hospital: Cleveland 83.6%, Hungary 79.7%, Switzerland 92.6%, VA Long Beach 76.3%. Only 35 women were in the test set, so their figures are uncertain.

**Limitations**
- Everyone in the data had already been referred for angiography, so the 55% disease rate is far above the general population's. The model should not be used to screen healthy people.
- In this group, people with **no** chest pain (asymptomatic) had high disease rates, so choosing "None" can raise the estimate.
- The earlier `heart.csv` (Kaggle) has 1,025 rows but only 302 unique patients. Its reported ~97% accuracy came from test rows that were copies of training rows. On unique rows that model scored ~74.5%.

## Safety features in the app
- An **emergency check** runs before every assessment. Heart attack or stroke warning signs show "Call 108 / 112" instead of a risk score.
- Values read from uploaded lab reports are shown for the user to check before they fill the form. The parser takes only the first number after a label and never takes a value from a reference range (see `reportParser.test.mjs`).
- Every result says it is an estimate, not a diagnosis.
