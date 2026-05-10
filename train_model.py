from __future__ import annotations

import numpy as np
from sklearn.linear_model import LogisticRegression


FEATURE_ORDER = [
    "sim_swap_count_30d",
    "hours_since_sim_change",
    "new_device",
    "location_mismatch",
    "failed_logins_24h",
    "transaction_amount",
]


def _generate_synthetic_data(n: int = 2000, seed: int = 42):
    rng = np.random.default_rng(seed)

    sim_swap_count = rng.integers(0, 4, n)
    hours_since_sim_change = rng.integers(0, 360, n)
    new_device = rng.integers(0, 2, n)
    location_mismatch = rng.integers(0, 2, n)
    failed_logins = rng.integers(0, 8, n)
    transaction_amount = rng.integers(100, 200000, n)

    # Fraud tendency score for label generation.
    risk_signal = (
        1.3 * sim_swap_count
        + 2.0 * (hours_since_sim_change < 24)
        + 1.8 * new_device
        + 1.8 * location_mismatch
        + 0.6 * failed_logins
        + 1.0 * (transaction_amount > 50000)
    )
    noise = rng.normal(0, 1.1, n)
    y = (risk_signal + noise >= 4.2).astype(int)

    x = np.column_stack(
        [
            sim_swap_count,
            hours_since_sim_change,
            new_device,
            location_mismatch,
            failed_logins,
            transaction_amount,
        ]
    )
    return x, y


import os
import joblib

def train_demo_model() -> LogisticRegression:
    model_path = "model.pkl"
    if os.path.exists(model_path):
        print("Loading existing model from disk...")
        return joblib.load(model_path)
    
    print("Training new model...")
    x, y = _generate_synthetic_data()
    model = LogisticRegression(max_iter=1000)
    model.fit(x, y)
    
    joblib.dump(model, model_path)
    print(f"Model saved to {model_path}")
    return model

def to_feature_vector(payload: dict) -> np.ndarray:
    values = []
    for key in FEATURE_ORDER:
        value = payload.get(key, 0)
        if key in {"new_device", "location_mismatch"}:
            value = int(bool(value))
        values.append(float(value))
    return np.array([values], dtype=float)
