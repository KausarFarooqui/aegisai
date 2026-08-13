"""
Tests for scripts/recompute_skill_trends.py — proves it actually rewrites
a stale trend_classification to match what the current classifier logic
produces from real linked AIOpportunity/AIAssessment data, not just that
it runs without error.
"""
import sys
import uuid
from pathlib import Path

import pytest
from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import recompute_skill_trends  # noqa: E402

from app.models import (  # noqa: E402
    Activity,
    AIAssessment,
    AIOpportunity,
    AutomationPotential,
    HumanAIResponsibility,
    ImpactBand,
    Industry,
    Process,
    Role,
    Skill,
    SkillTrend,
    ValueChain,
)


@pytest.fixture(autouse=True)
def _clean_tables(db):
    tables = [
        "graph_edges", "evidence", "future_responsibilities", "ai_assessments",
        "activity_ai_opportunities", "ai_opportunity_role_impacts",
        "ai_opportunity_skill_impacts", "ai_opportunities", "activity_roles",
        "role_skills", "activities", "processes", "roles", "skills",
        "research_sources", "value_chains", "organizations", "industries",
        "analysis_jobs",
    ]
    for t in tables:
        db.execute(text(f"TRUNCATE TABLE {t} CASCADE"))
    db.commit()
    yield


def test_recompute_corrects_a_stale_classification_to_match_real_signals(db, monkeypatch):
    industry = Industry(name=f"Test {uuid.uuid4()}")
    vc = ValueChain(name=f"Test VC {uuid.uuid4()}", industry=industry)
    process = Process(name="Test Process", value_chain=vc, source="seed")
    activity = Activity(name="Test Activity", process=process, source="seed")
    role = Role(title="Test Role", source="seed")
    skill = Skill(
        name="Test Skill", source="seed",
        trend_classification=SkillTrend.AI_AUGMENTED,  # deliberately WRONG/stale
        trend_rationale="stale rationale from before the classifier was fixed",
    )
    role.skills.append(skill)
    activity.roles.append(role)

    # Three AI_AUGMENTS opportunities, all HIGH/VERY_HIGH impact -> under
    # the CURRENT classifier this should compute to INCREASING (augment
    # dominant, 100% >= the 60% threshold), not the AI_AUGMENTED it's
    # currently stuck at.
    for i, band in enumerate([ImpactBand.HIGH, ImpactBand.VERY_HIGH, ImpactBand.HIGH]):
        opp = AIOpportunity(
            name=f"Opportunity {i}",
            automation_potential=AutomationPotential.MEDIUM,
            human_ai_responsibility=HumanAIResponsibility.AI_AUGMENTS,
            source="seed",
        )
        activity.ai_opportunities.append(opp)
        opp.affected_skills.append(skill)
        opp.assessment = AIAssessment(
            factor_repetitiveness=50, factor_data_availability=50, factor_predictability=50,
            factor_digitalization=50, factor_ai_capability_fit=50,
            factor_rationale={}, total_score=70.0, impact_band=band,
        )
        db.add(opp)

    db.add_all([industry, vc, process, activity, role, skill])
    db.commit()

    assert skill.trend_classification == SkillTrend.AI_AUGMENTED  # confirm the stale starting state

    monkeypatch.setattr(recompute_skill_trends, "SessionLocal", lambda: db)
    monkeypatch.setattr(db, "close", lambda: None)  # don't let the script close the test's session
    recompute_skill_trends.main()

    db.refresh(skill)
    assert skill.trend_classification == SkillTrend.INCREASING
    assert skill.trend_rationale != "stale rationale from before the classifier was fixed"


def test_recompute_handles_empty_database_gracefully(db, monkeypatch, capsys):
    monkeypatch.setattr(recompute_skill_trends, "SessionLocal", lambda: db)
    monkeypatch.setattr(db, "close", lambda: None)
    recompute_skill_trends.main()
    captured = capsys.readouterr()
    assert "nothing to recompute" in captured.out
