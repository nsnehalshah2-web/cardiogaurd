import pandas as pd
import numpy as np
import xgboost as xgb
import shap
import pickle
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report
import os

def train_and_save_model():
    data_path = os.path.join(os.path.dirname(__file__), 'heart_2.csv')
    
    try:
        df = pd.read_csv(data_path)
    except FileNotFoundError:
        print(f"Error: Could not find '{data_path}'. Please ensure heart_2.csv is in the ml/ directory.")
        return
    
    X = df[['age', 'sex', 'trestbps', 'chol', 'fbs', 'restecg', 'thalach', 'exang', 'oldpeak']]
    y = df['target']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    model = xgb.XGBClassifier(
        objective='binary:logistic',
        eval_metric='logloss',
        use_label_encoder=False,
        max_depth=5,
        learning_rate=0.05,
        n_estimators=150
    )
    model.fit(X_train_scaled, y_train)
    
    predictions = model.predict(X_test_scaled)
    print("Model Accuracy with heart_2.csv:", accuracy_score(y_test, predictions))
    print(classification_report(y_test, predictions))
    
    artifacts_dir = os.path.dirname(__file__)
    with open(os.path.join(artifacts_dir, 'model.pkl'), 'wb') as f:
        pickle.dump(model, f)
        
    with open(os.path.join(artifacts_dir, 'scaler.pkl'), 'wb') as f:
        pickle.dump(scaler, f)
        
    print("Model and Scaler updated successfully.")

if __name__ == "__main__":
    train_and_save_model()