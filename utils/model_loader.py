import os
import joblib
import numpy as np

MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "models")

_cost_model = None
_co2_model  = None
_le         = None


def _ensure_loaded():
    global _cost_model, _co2_model, _le
    if _cost_model is not None:
        return
    cost_path = os.path.join(MODELS_DIR, "cost_model.pkl")
    co2_path  = os.path.join(MODELS_DIR, "co2_model.pkl")
    le_path   = os.path.join(MODELS_DIR, "label_encoder.pkl")
    missing   = [p for p in [cost_path, co2_path, le_path] if not os.path.exists(p)]
    if missing:
        print("Models missing — auto-training...")
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
        from models.train_models import train
        train()
    _cost_model = joblib.load(cost_path)
    _co2_model  = joblib.load(co2_path)
    _le         = joblib.load(le_path)


def predict(material_type, strength_score, weight_capacity,
            biodegradability_score, recyclability_percentage):
    _ensure_loaded()
    try:
        type_enc = _le.transform([material_type])[0]
    except ValueError:
        type_enc = 0
    rng   = np.random.RandomState(42)
    noise = rng.normal(0, 0.05, (1, 3))
    base  = np.array([[type_enc, strength_score, weight_capacity,
                       biodegradability_score, recyclability_percentage]])
    X     = np.hstack([base, noise])
    cost  = float(_cost_model.predict(X)[0])
    co2   = float(_co2_model.predict(X)[0])
    return round(max(cost, 0.01), 4), round(max(co2, 0.01), 4)
