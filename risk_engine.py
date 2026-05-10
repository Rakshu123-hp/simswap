from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from train_model import train_demo_model, to_feature_vector


@dataclass
class RiskDecision:
    score: float
    ml_probability: float
    decision: str
    reasons: list[str]
    alert_required: bool


class RiskEngine:
    def __init__(self):
        self.model = train_demo_model()

    def evaluate(self, payload: Dict[str, Any]) -> RiskDecision:
        reasons: list[str] = []
        score = 0.0

        sim_swap_count = int(payload.get("sim_swap_count_30d", 0))
        hours_since_sim_change = float(payload.get("hours_since_sim_change", 9999))
        new_device = bool(payload.get("new_device", False))
        location_mismatch = bool(payload.get("location_mismatch", False))
        failed_logins = int(payload.get("failed_logins_24h", 0))
        amount = float(payload.get("transaction_amount", 0))

        # Rule-based checks (fast and explainable).
        if sim_swap_count >= 2:
            score += 18
            reasons.append("Multiple SIM swaps in last 30 days.")
        if hours_since_sim_change < 24:
            score += 25
            reasons.append("Activity soon after SIM change (<24h).")
        if new_device:
            score += 12
            reasons.append("Login from new device.")
        if location_mismatch:
            score += 15
            reasons.append("Location mismatch detected.")
        if failed_logins >= 4:
            score += 10
            reasons.append("High failed login count.")
        if amount > 50000:
            score += 12
            reasons.append("High-value transaction.")

        # ML probability blended into risk score.
        vector = to_feature_vector(payload)
        ml_probability = float(self.model.predict_proba(vector)[0][1])
        score += ml_probability * 30

        if score >= 65:
            decision = "BLOCK"
        elif score >= 35:
            decision = "STEP_UP"
        else:
            decision = "ALLOW"

        return RiskDecision(
            score=round(score, 2),
            ml_probability=round(ml_probability, 4),
            decision=decision,
            reasons=reasons or ["No strong fraud indicators."],
            alert_required=decision in {"STEP_UP", "BLOCK"},
        )
