"""
Deterministic Skill.trend_classification logic.

Recomputed (by the service layer, whenever an AIOpportunity linked to a
skill is created/updated — wired in Phase 5) from the set of AI
opportunities that affect the skill. Never set by the LLM directly and
never hand-typed during seeding — this is what makes "why is this skill
declining" a traceable, re-runnable calculation instead of a label someone
picked once.

REVISED after running the real 10-process seed script (see decision log,
"Post-Phase-6 — the skill-trend classifier couldn't reach two of its own
six categories"): the original design required a strict MAJORITY (>50%)
of a single responsibility type, which is the wrong statistical framing
when there are three possible types (automate/augment/human) — a
plurality (whichever is largest) is the correct signal of dominance, not
an absolute majority that none may reach if opinion splits three ways.
The original design also never implemented `INCREASING` at all, and
`EMERGING` was scoped so narrowly (zero linked opportunities) that it
became unreachable the moment a skill had any real usage data — against
real seeded data, every skill ended up classified `AI_AUGMENTED` with the
other two, more informative categories permanently silent.

The revised rule, still deliberately simple and stateable in one breath:

  1. No linked AI opportunities              -> UNCLASSIFIED (or EMERGING,
     if the skill was just introduced dynamically with nothing linked yet)
  2. Find the PLURALITY responsibility type among automate/augment/human
     (whichever ratio is largest). If two or more are tied for largest,
     there is no dominant signal              -> CHANGING
  3. If automate dominates:
       - and at least half the opportunities are HIGH/VERY_HIGH impact
                                                -> DECLINING
       - otherwise (automation-leaning but not yet clearly high-impact)
                                                -> CHANGING
  4. If augment dominates:
       - and at least 60% are HIGH/VERY_HIGH impact (a higher bar than
         DECLINING's 50%, since "increasing in importance" is a stronger
         claim than mere persistence)          -> INCREASING
       - otherwise                             -> AI_AUGMENTED
  5. If human dominates:
       - and fewer than half are HIGH/VERY_HIGH impact
                                                -> ENDURING_HUMAN
       - otherwise (human-led today, but touching a lot of high-impact
         work — genuinely unresolved direction) -> CHANGING
"""
from collections import Counter
from dataclasses import dataclass

from app.models import HumanAIResponsibility, ImpactBand, SkillTrend

# The higher bar for INCREASING vs. DECLINING/ENDURING_HUMAN's 0.5 is
# deliberate: claiming a skill is growing in strategic importance should
# require stronger evidence than claiming it merely persists or is merely
# at risk. Tune here if real seed data suggests otherwise — see decision
# log for the reasoning if this ever needs revisiting.
INCREASING_IMPACT_THRESHOLD = 0.6
DECLINING_IMPACT_THRESHOLD = 0.5
ENDURING_HUMAN_IMPACT_THRESHOLD = 0.5


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

    automate_count = responsibility_counts[HumanAIResponsibility.AI_AUTOMATES]
    augment_count = responsibility_counts[HumanAIResponsibility.AI_AUGMENTS]
    human_count = (
        responsibility_counts[HumanAIResponsibility.HUMAN_LED]
        + responsibility_counts[HumanAIResponsibility.HUMAN_APPROVAL_REQUIRED]
    )
    high_impact_ratio = high_impact_count / total

    ranked = sorted(
        [("automate", automate_count), ("augment", augment_count), ("human", human_count)],
        key=lambda pair: pair[1],
        reverse=True,
    )
    dominant_type, dominant_count = ranked[0]
    _, runner_up_count = ranked[1]

    if dominant_count <= runner_up_count:
        return (
            SkillTrend.CHANGING,
            f"No single responsibility type dominates this skill's linked AI "
            f"opportunities ({automate_count} automate / {augment_count} augment / "
            f"{human_count} human-led of {total} total) — signal is genuinely mixed.",
        )

    if dominant_type == "automate":
        if high_impact_ratio >= DECLINING_IMPACT_THRESHOLD:
            return (
                SkillTrend.DECLINING,
                f"{automate_count}/{total} linked AI opportunities are classified "
                f"AI-automates, and {high_impact_count}/{total} are rated HIGH/VERY_HIGH "
                f"impact.",
            )
        return (
            SkillTrend.CHANGING,
            f"{automate_count}/{total} linked AI opportunities are classified "
            f"AI-automates — automation-leaning, but only {high_impact_count}/{total} "
            f"are rated high impact, so this reads as an early shift, not a "
            f"confirmed decline yet.",
        )

    if dominant_type == "augment":
        if high_impact_ratio >= INCREASING_IMPACT_THRESHOLD:
            return (
                SkillTrend.INCREASING,
                f"{augment_count}/{total} linked AI opportunities are classified "
                f"AI-augments, and {high_impact_count}/{total} are rated HIGH/VERY_HIGH "
                f"impact — the skill remains essential and is increasingly central to "
                f"high-stakes AI-assisted work.",
            )
        return (
            SkillTrend.AI_AUGMENTED,
            f"{augment_count}/{total} linked AI opportunities are classified "
            f"AI-augments — the skill persists but its day-to-day application changes.",
        )

    # dominant_type == "human"
    if high_impact_ratio < ENDURING_HUMAN_IMPACT_THRESHOLD:
        return (
            SkillTrend.ENDURING_HUMAN,
            f"{human_count}/{total} linked AI opportunities remain human-led or "
            f"require human approval, with only {high_impact_count}/{total} rated "
            f"high impact.",
        )
    return (
        SkillTrend.CHANGING,
        f"{human_count}/{total} linked AI opportunities remain human-led or require "
        f"human approval, but {high_impact_count}/{total} are rated high impact — the "
        f"human role stays central for now, under increasing high-stakes AI pressure.",
    )
