"""
The deterministic AI Impact Score calculation.

This is the single function that turns five LLM-proposed factor estimates
into the number and band that get shown in the UI. It is a pure function —
no DB access, no LLM call, no side effects — so it can be tested exhaustively
and is the one thing in the whole pipeline you can point to and say "this
number is not something the AI made up, it's arithmetic."

The LLM's job (see app/intelligence/extraction.py, next) stops at proposing
factor_repetitiveness=90 with a one-line reason. Everything downstream of
that — the weighting, the banding, the persistence — is this function and
the code that calls it. That boundary is deliberate and is the answer to
"how do you prevent the AI from just making up a score."
"""
from dataclasses import dataclass

from app.models import ImpactBand
from app.scoring.config import IMPACT_BAND_THRESHOLDS, SCORING_WEIGHTS


@dataclass(frozen=True)
class ImpactFactors:
    repetitiveness: float
    data_availability: float
    predictability: float
    digitalization: float
    ai_capability_fit: float

    def __post_init__(self) -> None:
        for field_name, value in self.__dict__.items():
            if not (0.0 <= value <= 100.0):
                raise ValueError(
                    f"ImpactFactors.{field_name}={value} is out of range 0-100. "
                    "This should have been caught by Pydantic schema validation "
                    "on the LLM's output before it ever reached scoring — if "
                    "you're seeing this, the extraction schema's validation "
                    "range needs tightening, not this function."
                )


@dataclass(frozen=True)
class ImpactScoreResult:
    total_score: float
    impact_band: ImpactBand
    weighted_contributions: dict[str, float]
    """Per-factor contribution to the total (weight * value), so the UI's
    'why did the system reach this conclusion' panel can show a real
    breakdown instead of just the final number."""


def compute_impact_score(factors: ImpactFactors) -> ImpactScoreResult:
    """
    total = sum(weight[f] * factor[f] for f in factors)

    Weights come from SCORING_WEIGHTS (app/scoring/config.py) and are
    guaranteed to sum to 1.0 by test_scoring.py — so total_score is always
    on the same 0-100 scale as the inputs.
    """
    contributions = {
        "repetitiveness": SCORING_WEIGHTS["repetitiveness"] * factors.repetitiveness,
        "data_availability": SCORING_WEIGHTS["data_availability"] * factors.data_availability,
        "predictability": SCORING_WEIGHTS["predictability"] * factors.predictability,
        "digitalization": SCORING_WEIGHTS["digitalization"] * factors.digitalization,
        "ai_capability_fit": SCORING_WEIGHTS["ai_capability_fit"] * factors.ai_capability_fit,
    }
    total = round(sum(contributions.values()), 2)
    band = _classify_band(total)
    return ImpactScoreResult(total_score=total, impact_band=band, weighted_contributions=contributions)


def _classify_band(total_score: float) -> ImpactBand:
    for lower_bound, band in IMPACT_BAND_THRESHOLDS:
        if total_score >= lower_bound:
            return band
    # Unreachable given IMPACT_BAND_THRESHOLDS' final (0.0, LOW) entry, but
    # fail loudly rather than silently return None if that invariant ever breaks.
    raise RuntimeError(f"No impact band matched for total_score={total_score}")
