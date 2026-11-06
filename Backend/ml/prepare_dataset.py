"""Build heart_disease_uci.csv from the original UCI Heart Disease database.

Source: Janosi, Steinbrunn, Pfisterer & Detrano (1988), UCI Machine Learning Repository,
https://archive.ics.uci.edu/dataset/45/heart+disease

The database has 920 real patient records from four hospitals:
  Cleveland Clinic (303), Hungarian Institute of Cardiology, Budapest (294),
  University Hospitals Zurich & Basel, Switzerland (123), VA Medical Center, Long Beach (200).

Run once:  python prepare_dataset.py
"""
import os
import urllib.request

import numpy as np
import pandas as pd

BASE_URL = "https://archive.ics.uci.edu/ml/machine-learning-databases/heart-disease/processed.{}.data"
SOURCES = {
    "cleveland": "Cleveland",
    "hungarian": "Hungary",
    "switzerland": "Switzerland",
    "va": "VA Long Beach",
}
COLUMNS = ['age', 'sex', 'cp', 'trestbps', 'chol', 'fbs', 'restecg', 'thalach',
           'exang', 'oldpeak', 'slope', 'ca', 'thal', 'num']
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), 'heart_disease_uci.csv')


def build_dataset() -> pd.DataFrame:
    frames = []
    for key, name in SOURCES.items():
        with urllib.request.urlopen(BASE_URL.format(key)) as response:
            frame = pd.read_csv(response, header=None, names=COLUMNS, na_values='?')
        frame['source'] = name
        frames.append(frame)
    data = pd.concat(frames, ignore_index=True)

    # A value of 0 for cholesterol or blood pressure means "not measured" in this database
    # (all Swiss records have chol = 0), so store it as missing instead of a real zero.
    data.loc[data['chol'] == 0, 'chol'] = np.nan
    data.loc[data['trestbps'] == 0, 'trestbps'] = np.nan

    # num is 0 (no disease) to 4 (severe); any narrowing > 50% counts as disease.
    data['target'] = (data['num'] > 0).astype(int)
    return data.drop(columns=['num']).drop_duplicates().reset_index(drop=True)


if __name__ == "__main__":
    dataset = build_dataset()
    dataset.to_csv(OUTPUT_PATH, index=False)
    print(f"Saved {len(dataset)} patients to {OUTPUT_PATH}")
    print(dataset.groupby('source')['target'].agg(['count', 'mean']).rename(columns={'mean': 'disease_rate'}))
