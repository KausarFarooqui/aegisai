"""
Pure unit tests for app/scoring — no DB, no network. These should run in
milliseconds and are the fastest possible check that the scoring math is
right before anything touches a live database.
"""
import pytest

from app.models import HumanAIResponsibility, ImpactBand, SkillTrend
from app.scoring.config import SCORING_WEIGHTS
from app.scoring.impact_score import ImpactFactors, compute_impact_score
from app.scoring.skill_trend import SkillOpportunitySignal, classify_skill_trend


def test_scoring_weights_sum_to_one():
    """If this ever fails after someone edits config.py, the total_score
    scale silently breaks — this is the guardrail."""
    assert round(sum(SCORING_WEIGHTS.values()), 6) == 1.0


def test_compute_impact_score_matches_hand_calculation():
    factors = ImpactFactors(
        repetitiveness=90, data_availability=85, predictability=80,
        digitalization=75, ai_capability_fit=88,
    )
    expected = round(0.30 * 90 + 0.20 * 85 + 0.20 * 80 + 0.15 * 75 + 0.15 * 88, 2)
    result = compute_impact_score(factors)
    assert result.total_score == expected == 84.45
    assert result.impact_band == ImpactBand.VERY_HIGH  # 84.45 >= 81


def test_impact_score_contributions_sum_to_total():
    factors = ImpactFactors(50, 50, 50, 50, 50)
    result = compute_impact_score(factors)
    assert round(sum(result.weighted_contributions.values()), 2) == result.total_score
    assert result.total_score == 50.0
    assert result.impact_band == ImpactBand.MEDIUM


@pytest.mark.parametrize(
    "score,expected_band",
    [
        (0, ImpactBand.LOW),
        (30, ImpactBand.LOW),
        (30.99, ImpactBand.LOW),
        (31, ImpactBand.MEDIUM),
        (60, ImpactBand.MEDIUM),
        (61, ImpactBand.HIGH),
        (80, ImpactBand.HIGH),
        (81, ImpactBand.VERY_HIGH),
        (100, ImpactBand.VERY_HIGH),
    ],
)
def test_impact_band_boundaries(score, expected_band):
    """All five factors set equal to `score` so total_score == score exactly
    (weights sum to 1.0), directly proving each documented boundary."""
    factors = ImpactFactors(score, score, score, score, score)
    result = compute_impact_score(factors)
    assert result.total_score == score
    assert result.impact_band == expected_band


def test_impact_factors_reject_out_of_range_values():
    with pytest.raises(ValueError):
        ImpactFactors(101, 50, 50, 50, 50)
    with pytest.raises(ValueError):
        ImpactFactors(50, -1, 50, 50, 50)


# --- Skill trend classification ---

def test_skill_trend_unclassified_when_no_signals():
    trend, rationale = classify_skill_trend([])
    assert trend == SkillTrend.UNCLASSIFIED


def test_skill_trend_emerging_when_new_and_dynamic_with_no_signals():
    trend, rationale = classify_skill_trend([], skill_is_newly_dynamic=True)
    assert trend == SkillTrend.EMERGING


def test_skill_trend_declining_when_mostly_automated_and_high_impact():
    signals = [
        SkillOpportunitySignal(HumanAIResponsibility.AI_AUTOMATES, ImpactBand.HIGH),
        SkillOpportunitySignal(HumanAIResponsibility.AI_AUTOMATES, ImpactBand.VERY_HIGH),
        SkillOpportunitySignal(HumanAIResponsibility.AI_AUGMENTS, ImpactBand.MEDIUM),
    ]
    trend, rationale = classify_skill_trend(signals)
    assert trend == SkillTrend.DECLINING
    assert "2/3" in rationale


def test_skill_trend_ai_augmented_when_mostly_augments():
    signals = [
        SkillOpportunitySignal(HumanAIResponsibility.AI_AUGMENTS, ImpactBand.HIGH),
        SkillOpportunitySignal(HumanAIResponsibility.AI_AUGMENTS, ImpactBand.MEDIUM),
        SkillOpportunitySignal(HumanAIResponsibility.HUMAN_LED, ImpactBand.LOW),
    ]
    trend, rationale = classify_skill_trend(signals)
    assert trend == SkillTrend.AI_AUGMENTED


def test_skill_trend_enduring_human_when_mostly_human_led_and_low_impact():
    signals = [
        SkillOpportunitySignal(HumanAIResponsibility.HUMAN_LED, ImpactBand.LOW),
        SkillOpportunitySignal(HumanAIResponsibility.HUMAN_APPROVAL_REQUIRED, ImpactBand.MEDIUM),
        SkillOpportunitySignal(HumanAIResponsibility.AI_AUGMENTS, ImpactBand.LOW),
    ]
    trend, rationale = classify_skill_trend(signals)
    assert trend == SkillTrend.ENDURING_HUMAN


def test_skill_trend_changing_when_signal_is_mixed():
    signals = [
        SkillOpportunitySignal(HumanAIResponsibility.AI_AUTOMATES, ImpactBand.LOW),
        SkillOpportunitySignal(HumanAIResponsibility.HUMAN_LED, ImpactBand.HIGH),
    ]
    trend, rationale = classify_skill_trend(signals)
    assert trend == SkillTrend.CHANGING


def test_skill_trend_increasing_when_augment_dominant_and_strongly_high_impact():
    """The category the original design never implemented at all — augment
    dominates AND a strong majority (>=60%) is high/very-high impact."""
    signals = [
        SkillOpportunitySignal(HumanAIResponsibility.AI_AUGMENTS, ImpactBand.HIGH),
        SkillOpportunitySignal(HumanAIResponsibility.AI_AUGMENTS, ImpactBand.VERY_HIGH),
        SkillOpportunitySignal(HumanAIResponsibility.AI_AUGMENTS, ImpactBand.HIGH),
        SkillOpportunitySignal(HumanAIResponsibility.HUMAN_LED, ImpactBand.LOW),
    ]
    trend, rationale = classify_skill_trend(signals)
    assert trend == SkillTrend.INCREASING
    assert "3/4" in rationale


def test_skill_trend_ai_augmented_not_increasing_when_below_impact_threshold():
    """Same augment-dominant shape as the INCREASING case, but impact ratio
    sits below 60% — must land on AI_AUGMENTED, not INCREASING. Proves the
    two categories are actually distinguishable, not just aliases."""
    signals = [
        SkillOpportunitySignal(HumanAIResponsibility.AI_AUGMENTS, ImpactBand.HIGH),
        SkillOpportunitySignal(HumanAIResponsibility.AI_AUGMENTS, ImpactBand.LOW),
        SkillOpportunitySignal(HumanAIResponsibility.AI_AUGMENTS, ImpactBand.MEDIUM),
        SkillOpportunitySignal(HumanAIResponsibility.HUMAN_LED, ImpactBand.LOW),
    ]
    trend, rationale = classify_skill_trend(signals)
    assert trend == SkillTrend.AI_AUGMENTED


def test_skill_trend_changing_when_automate_dominant_but_impact_not_yet_high():
    """New branch: automation-type opportunities dominate, but impact
    hasn't cleared the bar for a confirmed DECLINING call yet."""
    signals = [
        SkillOpportunitySignal(HumanAIResponsibility.AI_AUTOMATES, ImpactBand.LOW),
        SkillOpportunitySignal(HumanAIResponsibility.AI_AUTOMATES, ImpactBand.MEDIUM),
        SkillOpportunitySignal(HumanAIResponsibility.HUMAN_LED, ImpactBand.LOW),
    ]
    trend, rationale = classify_skill_trend(signals)
    assert trend == SkillTrend.CHANGING
    assert "not a confirmed decline" in rationale


def test_skill_trend_changing_when_human_dominant_but_impact_is_high():
    """New branch: human-led/approval opportunities dominate, but a
    majority are rated high impact — genuinely unresolved direction."""
    signals = [
        SkillOpportunitySignal(HumanAIResponsibility.HUMAN_LED, ImpactBand.HIGH),
        SkillOpportunitySignal(HumanAIResponsibility.HUMAN_APPROVAL_REQUIRED, ImpactBand.VERY_HIGH),
        SkillOpportunitySignal(HumanAIResponsibility.AI_AUGMENTS, ImpactBand.LOW),
    ]
    trend, rationale = classify_skill_trend(signals)
    assert trend == SkillTrend.CHANGING
    assert "under increasing high-stakes AI pressure" in rationale


def test_skill_trend_plurality_not_majority_still_declining():
    """The core statistical fix: automate has exactly 50% (2 of 4) — under
    the OLD design's strict `> 0.5` majority check, this would NOT have
    qualified (0.5 is not greater than 0.5) and would have fallen through
    every other check to CHANGING. Under the new plurality rule, automate
    still strictly outranks both other types individually (2 vs. 1 vs. 1),
    which is the correct signal of dominance."""
    signals = [
        SkillOpportunitySignal(HumanAIResponsibility.AI_AUTOMATES, ImpactBand.HIGH),
        SkillOpportunitySignal(HumanAIResponsibility.AI_AUTOMATES, ImpactBand.VERY_HIGH),
        SkillOpportunitySignal(HumanAIResponsibility.AI_AUGMENTS, ImpactBand.HIGH),
        SkillOpportunitySignal(HumanAIResponsibility.HUMAN_LED, ImpactBand.LOW),
    ]
    trend, rationale = classify_skill_trend(signals)
    assert trend == SkillTrend.DECLINING
    assert "2/4" in rationale


def test_skill_trend_exact_three_way_tie_is_changing():
    """No responsibility type can claim dominance when all three are
    equally represented."""
    signals = [
        SkillOpportunitySignal(HumanAIResponsibility.AI_AUTOMATES, ImpactBand.HIGH),
        SkillOpportunitySignal(HumanAIResponsibility.AI_AUGMENTS, ImpactBand.HIGH),
        SkillOpportunitySignal(HumanAIResponsibility.HUMAN_LED, ImpactBand.HIGH),
    ]
    trend, rationale = classify_skill_trend(signals)
    assert trend == SkillTrend.CHANGING
    assert "No single responsibility type dominates" in rationale
