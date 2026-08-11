"""
Scoring configuration — the ONE place the weighting formula lives.

Kept separate from the scoring function itself so the formula can be tuned
(e.g. after seeing how the first batch of seed data scores) without
touching any logic, and so `scoring_model_version` has something concrete
to point at if the weights ever change.
"""
from app.models import ImpactBand

# Must sum to 1.0 — enforced by a test, not just a comment.
SCORING_WEIGHTS: dict[str, float] = {
    "repetitiveness": 0.30,
    "data_availability": 0.20,
    "predictability": 0.20,
    "digitalization": 0.15,
    "ai_capability_fit": 0.15,
}

SCORING_MODEL_VERSION = "v1"

# Inclusive lower bounds. A score of exactly 30 is LOW, 31 is MEDIUM, etc.
IMPACT_BAND_THRESHOLDS: list[tuple[float, ImpactBand]] = [
    (81.0, ImpactBand.VERY_HIGH),
    (61.0, ImpactBand.HIGH),
    (31.0, ImpactBand.MEDIUM),
    (0.0, ImpactBand.LOW),
]
