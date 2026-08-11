"""
Deterministic Skill.trend_classification logic.

Recomputed (by the service layer, whenever an AIOpportunity linked to a
skill is created/updated — wired in Phase 5) from the set of AI
opportunities that affect the skill. Never set by the LLM directly and
never hand-typed during seeding — this is what makes "why is this skill
declining" a traceable, re-runnable calculation instead of a label someone
picked once.

The classification rule (deliberately simple and explainable — this is
exactly the kind of logic you want to be able to state in one breath
during an interview, not something with a dozen tunable magic numbers):

  - No linked AI opportunities at all           -> UNCLASSIFIED
  - Majority AI_AUTOMATES + majority HIGH/VERY_HIGH impact -> DECLINING
  - Majority AI_AUGMENTS                        -> AI_AUGMENTED
  - Majority HUMAN_LED or HUMAN_APPROVAL_REQUIRED,
    with only LOW/MEDIUM automation impact       -> ENDURING_HUMAN
  - A skill introduced via the dynamic pipeline (source="dynamic") with no
    opportunities yet linked, in a domain context that implies AI-adjacent
    work (left as a hook — see EMERGING note below)  -> EMERGING
  - Anything with a mixed/tied signal            -> CHANGING
"""
from collections import Counter
from dataclasses import dataclass

from app.models import HumanAIResponsibility, ImpactBand, SkillTrend


@dataclass(frozen=True)
class SkillOpportunitySignal:
    """One (AIOpportunity, its AIAssessment) pair affecting a given skill —
    the minimal data this function needs, decoupled from ORM objects so it
    stays a pure, easily unit-testable function."""
    human_ai_responsibility: HumanAIResponsibility
    impact_band: ImpactBand


def classify_skill_trend(
    signals: list[SkillOpportunitySignal],
    skill_is_newly_dynamic: bool = False,
) -> tuple[SkillTrend, str]:
    """
    Returns (trend, rationale) — rationale is stored verbatim in
    Skill.trend_rationale so the UI can show *why* without re-deriving it.
    """
    if not signals:
        if skill_is_newly_dynamic:
            return (
                SkillTrend.EMERGING,
                "Introduced through dynamic analysis with no AI opportunities "
                "linked yet — provisionally classified emerging pending "
                "further linkage.",
            )
        return SkillTrend.UNCLASSIFIED, "No AI opportunities are linked to this skill yet."

    high_impact_bands = {ImpactBand.HIGH, ImpactBand.VERY_HIGH}
    responsibility_counts = Counter(s.human_ai_responsibility for s in signals)
    high_impact_count = sum(1 for s in signals if s.impact_band in high_impact_bands)
    total = len(signals)

    automate_ratio = responsibility_counts[HumanAIResponsibility.AI_AUTOMATES] / total
    augment_ratio = responsibility_counts[HumanAIResponsibility.AI_AUGMENTS] / total
    human_ratio = (
        responsibility_counts[HumanAIResponsibility.HUMAN_LED]
        + responsibility_counts[HumanAIResponsibility.HUMAN_APPROVAL_REQUIRED]
    ) / total
    high_impact_ratio = high_impact_count / total

    if automate_ratio > 0.5 and high_impact_ratio > 0.5:
        return (
            SkillTrend.DECLINING,
            f"{responsibility_counts[HumanAIResponsibility.AI_AUTOMATES]}/{total} linked AI "
            f"opportunities are classified AI-automates with HIGH/VERY_HIGH impact.",
        )

    if augment_ratio > 0.5:
        return (
            SkillTrend.AI_AUGMENTED,
            f"{responsibility_counts[HumanAIResponsibility.AI_AUGMENTS]}/{total} linked AI "
            f"opportunities are classified AI-augments — the skill persists but its "
            f"day-to-day application changes.",
        )

    if human_ratio > 0.5 and high_impact_ratio <= 0.5:
        return (
            SkillTrend.ENDURING_HUMAN,
            f"{responsibility_counts[HumanAIResponsibility.HUMAN_LED] + responsibility_counts[HumanAIResponsibility.HUMAN_APPROVAL_REQUIRED]}/{total} "
            f"linked AI opportunities remain human-led or require human approval, "
            f"with only low/medium automation impact.",
        )

    return (
        SkillTrend.CHANGING,
        f"Linked AI opportunities are mixed across automation types and impact "
        f"levels ({dict(responsibility_counts)}) — no single trend dominates.",
    )
