"""Build framingham.csv for the home screening model.

Source: the Framingham Heart Study teaching dataset (4,240 participants from Framingham,
Massachusetts, followed for 10 years; TenYearCHD = developed coronary heart disease within 10 years).
The teaching dataset is distributed by NHLBI BioLINCC; this script fetches the widely used
public copy and checks that it matches the published size and outcome counts.

Run once:  python prepare_framingham.py
"""
import io
import os
import urllib.request

import pandas as pd

SOURCE_URL = "https://raw.githubusercontent.com/GauravPadawe/Framingham-Heart-Study/master/framingham.csv"
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), 'framingham.csv')


def build_dataset() -> pd.DataFrame:
    with urllib.request.urlopen(SOURCE_URL) as response:
        raw = response.read().decode('utf-8')
    # The public copy uses old Mac (CR-only) line endings.
    data = pd.read_csv(io.StringIO(raw.replace('\r\n', '\n').replace('\r', '\n')))
    if len(data) != 4240 or int(data['TenYearCHD'].sum()) != 644:
        raise ValueError("Downloaded file does not match the Framingham teaching dataset (4240 rows, 644 cases)")
    return data


if __name__ == "__main__":
    dataset = build_dataset()
    dataset.to_csv(OUTPUT_PATH, index=False)
    print(f"Saved {len(dataset)} participants to {OUTPUT_PATH} ({int(dataset['TenYearCHD'].sum())} developed CHD)")
