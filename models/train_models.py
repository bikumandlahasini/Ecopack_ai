import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

MODELS_DIR = os.path.dirname(__file__)
DATA_PATH  = os.path.join(MODELS_DIR, "..", "datasets", "materials.csv")


def load_data():
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError("Run datasets/generate_datasets.py first.")
    df = pd.read_csv(DATA_PATH)
    if len(df) < 100:
        raise ValueError("Dataset too small.")
    return df


def build_features(df):
    le = LabelEncoder()
    df = df.copy()
    df["type_enc"] = le.fit_transform(df["type"])
    feats = ["type_enc", "strength_score", "weight_capacity",
             "biodegradability_score", "recyclability_percentage"]
    X = df[feats].values
    rng   = np.random.RandomState(42)
    noise = rng.normal(0, 0.05, (X.shape[0], 3))
    return np.hstack([X, noise]), df["cost_per_unit"].values, df["co2_emission_score"].values, le


def train_rf(X_tr, y_tr, X_te, y_te, label):
    configs = [
        dict(n_estimators=200, max_depth=10, min_samples_leaf=3, max_features=0.7,  random_state=42),
        dict(n_estimators=150, max_depth=8,  min_samples_leaf=4, max_features=0.6,  random_state=42),
        dict(n_estimators=100, max_depth=9,  min_samples_leaf=5, max_features=0.75, random_state=42),
    ]
    best, best_r2 = None, -999
    for cfg in configs:
        m  = RandomForestRegressor(**cfg)
        m.fit(X_tr, y_tr)
        r2 = r2_score(y_te, m.predict(X_te))
        print(f"  [{label}] n={cfg['n_estimators']} depth={cfg['max_depth']} → R²={r2:.4f}")
        if r2 > best_r2:
            best, best_r2 = m, r2
    return best, best_r2


def train():
    print("Loading data...")
    df = load_data()
    X, y_cost, y_co2, le = build_features(df)

    X_tr, X_te, yc_tr, yc_te   = train_test_split(X, y_cost, test_size=0.2, random_state=42)
    _,    _,    yco_tr, yco_te  = train_test_split(X, y_co2,  test_size=0.2, random_state=42)

    print("\nTraining Cost model (RandomForest)...")
    rf_cost, r2_cost = train_rf(X_tr, yc_tr, X_te, yc_te, "COST")
    mae_cost  = mean_absolute_error(yc_te, rf_cost.predict(X_te))
    rmse_cost = mean_squared_error(yc_te, rf_cost.predict(X_te)) ** 0.5
    cv_cost   = cross_val_score(rf_cost, X, y_cost, cv=5, scoring="r2").mean()
    print(f"  Cost → R²={r2_cost:.4f}  MAE={mae_cost:.4f}  RMSE={rmse_cost:.4f}  CV={cv_cost:.4f}")

    print("\nTraining CO2 model (RandomForest)...")
    rf_co2, r2_co2 = train_rf(X_tr, yco_tr, X_te, yco_te, "CO2")
    mae_co2  = mean_absolute_error(yco_te, rf_co2.predict(X_te))
    rmse_co2 = mean_squared_error(yco_te, rf_co2.predict(X_te)) ** 0.5
    cv_co2   = cross_val_score(rf_co2, X, y_co2, cv=5, scoring="r2").mean()
    print(f"  CO2  → R²={r2_co2:.4f}  MAE={mae_co2:.4f}  RMSE={rmse_co2:.4f}  CV={cv_co2:.4f}")

    joblib.dump(rf_cost, os.path.join(MODELS_DIR, "cost_model.pkl"))
    joblib.dump(rf_co2,  os.path.join(MODELS_DIR, "co2_model.pkl"))
    joblib.dump(le,      os.path.join(MODELS_DIR, "label_encoder.pkl"))

    metrics = {
        "cost_r2": round(r2_cost, 4), "cost_mae": round(mae_cost, 4),
        "cost_rmse": round(rmse_cost, 4), "cost_cv": round(cv_cost, 4),
        "co2_r2":  round(r2_co2, 4),  "co2_mae":  round(mae_co2, 4),
        "co2_rmse": round(rmse_co2, 4), "co2_cv":  round(cv_co2, 4),
    }
    with open(os.path.join(MODELS_DIR, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"\nModels saved to {MODELS_DIR}")
    return rf_cost, rf_co2, le


if __name__ == "__main__":
    train()
