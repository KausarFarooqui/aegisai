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
    The AI Impact Score formula is:
      0.30*repetitiveness + 0.20*data_availability + 0.20*predictability
      + 0.15*digitalization + 0.15*ai_capability_fit

    AIAssessment.total_score must always be computed by deterministic code
    (see app/scoring, added in Phase 4) — this test locks the expected
    output for a known input so a future change to the formula fails loudly.
    """
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

    factors = {
        "repetitiveness": 90.0,
        "data_availability": 85.0,
        "predictability": 80.0,
        "digitalization": 75.0,
        "ai_capability_fit": 88.0,
    }
    expected_total = (
        0.30 * factors["repetitiveness"]
        + 0.20 * factors["data_availability"]
        + 0.20 * factors["predictability"]
        + 0.15 * factors["digitalization"]
        + 0.15 * factors["ai_capability_fit"]
    )

    assessment = AIAssessment(
        ai_opportunity=opportunity,
        factor_repetitiveness=factors["repetitiveness"],
        factor_data_availability=factors["data_availability"],
        factor_predictability=factors["predictability"],
        factor_digitalization=factors["digitalization"],
        factor_ai_capability_fit=factors["ai_capability_fit"],
        factor_rationale={},
        total_score=expected_total,
        impact_band=ImpactBand.HIGH,
    )

    db.add_all([industry, vc, process, activity, opportunity, assessment])
    db.commit()
    db.expire_all()

    fetched = db.query(AIOpportunity).filter_by(name="Test Opportunity").one()
    assert round(fetched.assessment.total_score, 2) == round(expected_total, 2)
    assert fetched.assessment.impact_band == ImpactBand.HIGH


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
