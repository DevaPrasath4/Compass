import os

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split

MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
os.makedirs(MODEL_DIR, exist_ok=True)
DATA_PATH = os.path.join(os.path.dirname(__file__), "datasets", "synthetic_monthly_history.csv")


def _feature_from_month(month_no: int):
    angle = (month_no - 1) / 12.0 * 2 * np.pi
    return np.sin(angle), np.cos(angle)


def train_forecast_model():
    df = pd.read_csv(DATA_PATH)
    rows = []
    for _, row in df.iterrows():
        month_sin, month_cos = _feature_from_month(int(row["month"]))
        rows.append({
            "month_sin": month_sin,
            "month_cos": month_cos,
            "category": row["category"],
            "location": row["location"],
            "complaints": float(row["complaints"]),
        })
    training = pd.DataFrame(rows)
    cat_dummies = pd.get_dummies(training[["category", "location"]], dtype=float)
    X = pd.concat([training[["month_sin", "month_cos"]].reset_index(drop=True), cat_dummies.reset_index(drop=True)], axis=1)
    y = training["complaints"].reset_index(drop=True)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = LinearRegression()
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    print(f"[forecast model] MAE: {mae:.3f}")
    joblib.dump(model, os.path.join(MODEL_DIR, "forecast_model.joblib"))
    return model


if __name__ == "__main__":
    train_forecast_model()
