"""
Relationship-integrity tests for the core domain model.

This is the automated version of the manual round-trip already run against
a live Postgres+pgvector instance during Phase 3 verification (Industry ->
ValueChain -> Process -> Activity -> Role -> Skill, plus AIOpportunity ->
AIAssessment scoring). Codified here so it runs on every future change,
not just once by hand.
"""
from app.models import (
    Industry,
    Organization,
    ValueChain,
    Process,
    Activity,
    Role,
    Skill,
    AIOpportunity,
    AIAssessment,
    AutomationPotential,
    HumanAIResponsibility,
    ImpactBand,
)


def test_full_hierarchy_round_trip(db):
    industry = Industry(name="Banking & Financial Services (test)")
    org = Organization(name="Northstar Bank (test)", industry=industry, is_fictional=True)
    vc = ValueChain(name="Retail Lending (test)", industry=industry, sequence_order=1)
    process = Process(name="Loan Underwriting (test)", value_chain=vc, source="seed")
    activity = Activity(name="Manual document review (test)", process=process, source="seed")

    role = Role(title="Credit Analyst (test)", source="seed")
    skill = Skill(name="Credit Risk Assessment (test)", source="seed")
    role.skills.append(skill)
    activity.roles.append(role)

    db.add_all([industry, org, vc, process, activity, role, skill])
    db.commit()
    db.expire_all()

    fetched = db.query(Role).filter_by(title="Credit Analyst (test)").one()
    assert [s.name for s in fetched.skills] == ["Credit Risk Assessment (test)"]
    assert [a.name for a in fetched.activities] == ["Manual document review (test)"]


def test_ai_assessment_scoring_matches_weighted_formula(db):
    """
    AIAssessment.total_score and impact_band must always be produced by
    app.scoring.compute_impact_score — never hand-set. This test persists
    a real assessment using that function's output, then confirms the DB
    round-trips it unchanged.
    """
    from app.scoring.impact_score import ImpactFactors, compute_impact_score

    industry = Industry(name="Test Industry for Scoring")
    vc = ValueChain(name="Test Value Chain", industry=industry)
    process = Process(name="Test Process", value_chain=vc, source="dynamic")
    activity = Activity(name="Test Activity", process=process, source="dynamic")

    opportunity = AIOpportunity(
        name="Test Opportunity",
        automation_potential=AutomationPotential.HIGH,
        human_ai_responsibility=HumanAIResponsibility.AI_AUTOMATES,
        source="dynamic",
    )
    activity.ai_opportunities.append(opportunity)

    factors = ImpactFactors(
        repetitiveness=90.0, data_availability=85.0, predictability=80.0,
        digitalization=75.0, ai_capability_fit=88.0,
    )
    scored = compute_impact_score(factors)
    assert scored.total_score == 84.45
    assert scored.impact_band == ImpactBand.VERY_HIGH  # not HIGH — 84.45 >= 81

    assessment = AIAssessment(
        ai_opportunity=opportunity,
        factor_repetitiveness=factors.repetitiveness,
        factor_data_availability=factors.data_availability,
        factor_predictability=factors.predictability,
        factor_digitalization=factors.digitalization,
        factor_ai_capability_fit=factors.ai_capability_fit,
        factor_rationale={},
        total_score=scored.total_score,
        impact_band=scored.impact_band,
    )

    db.add_all([industry, vc, process, activity, opportunity, assessment])
    db.commit()
    db.expire_all()

    fetched = db.query(AIOpportunity).filter_by(name="Test Opportunity").one()
    assert fetched.assessment.total_score == 84.45
    assert fetched.assessment.impact_band == ImpactBand.VERY_HIGH


def test_enum_columns_store_lowercase_values(db):
    """
    Regression test for the bug caught during live-DB verification: without
    pg_enum()'s values_callable, SQLAlchemy stores the enum NAME ("HIGH")
    instead of the VALUE ("high"). This asserts the fix holds.
    """
    industry = Industry(name="Enum Regression Test Industry")
    vc = ValueChain(name="Enum Regression VC", industry=industry)
    process = Process(name="Enum Regression Process", value_chain=vc, source="dynamic")
    activity = Activity(name="Enum Regression Activity", process=process, source="dynamic")
    opportunity = AIOpportunity(
        name="Enum Regression Opportunity",
        automation_potential=AutomationPotential.HIGH,
        human_ai_responsibility=HumanAIResponsibility.AI_AUTOMATES,
        source="dynamic",
    )
    activity.ai_opportunities.append(opportunity)
    db.add_all([industry, vc, process, activity, opportunity])
    db.commit()

    from sqlalchemy import text

    raw_value = db.execute(
        text("SELECT automation_potential FROM ai_opportunities WHERE name = :n"),
        {"n": "Enum Regression Opportunity"},
    ).scalar_one()
    assert raw_value == "high"  # not "HIGH"
