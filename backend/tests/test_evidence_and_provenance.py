"""
Tests for app/services/evidence_service.py and the pipeline's `source`
parameter (seed vs dynamic provenance). Uses the same FakeEmbeddingProvider
pattern as test_analysis_pipeline.py so these stay network-independent.
"""
import uuid
from datetime import date

import pytest
from sqlalchemy import text

from app.models import Evidence, Industry, RelatedEntityType, ResearchSource, SourceType, ValueChain
from app.services.evidence_service import EvidenceService
from tests.test_analysis_pipeline import (
    FakeEmbeddingProvider,
    ScriptedLLMProvider,
    _valid_extraction_payload,
)
from app.workers.analysis_pipeline import ProcessAnalysisPipeline


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


@pytest.fixture()
def value_chain(db) -> ValueChain:
    industry = Industry(name=f"Test Banking {uuid.uuid4()}")
    vc = ValueChain(name=f"Test Retail Lending {uuid.uuid4()}", industry=industry, sequence_order=1)
    db.add_all([industry, vc])
    db.commit()
    return vc


def _make_research_source(
    db, embedder: FakeEmbeddingProvider, title: str, summary: str, embed_text: str | None = None
) -> ResearchSource:
    source = ResearchSource(
        title=title,
        url="https://example.com/test-source",
        source_type=SourceType.RESEARCH,
        retrieved_date=date(2026, 8, 12),
        summary=summary,
        embedding=embedder.encode(embed_text if embed_text is not None else title),
    )
    db.add(source)
    db.commit()
    return source


# ----------------------------------------------------------------------
# EvidenceService unit tests
# ----------------------------------------------------------------------

def test_finds_evidence_when_a_relevant_source_exists(db, value_chain):
    embedder = FakeEmbeddingProvider()
    opportunity_name = "AI Automated Document Extraction"
    opportunity_description = ""
    # The fake embedder hashes the literal string, so the research source
    # is embedded with the exact text the service will query with
    # (f"{name}. {description}") — a real semantic model wouldn't need this,
    # but this fake one has no notion of near-equality.
    query_text = f"{opportunity_name}. {opportunity_description}".strip()
    _make_research_source(
        db, embedder,
        title="AI Automated Document Extraction",
        summary="Describes how AI extracts structured data from documents.",
        embed_text=query_text,
    )

    from app.models import AIOpportunity, AutomationPotential, HumanAIResponsibility

    opportunity = AIOpportunity(
        id=uuid.uuid4(),
        name=opportunity_name,
        description=opportunity_description,
        automation_potential=AutomationPotential.HIGH,
        human_ai_responsibility=HumanAIResponsibility.AI_AUTOMATES,
        source="dynamic",
    )

    service = EvidenceService(db, embedder, relevance_threshold=0.86)
    evidence = service.find_evidence_for_opportunity(opportunity)

    assert evidence is not None
    assert evidence.research_source.title == "AI Automated Document Extraction"
    assert evidence.related_entity_type == RelatedEntityType.AI_OPPORTUNITY
    assert evidence.related_entity_id == opportunity.id
    assert evidence.relevance_score > 0.86


def test_returns_none_when_no_research_sources_exist(db):
    from app.models import AIOpportunity, AutomationPotential, HumanAIResponsibility

    embedder = FakeEmbeddingProvider()
    opportunity = AIOpportunity(
        id=uuid.uuid4(), name="Some Opportunity", description="",
        automation_potential=AutomationPotential.MEDIUM,
        human_ai_responsibility=HumanAIResponsibility.AI_AUGMENTS, source="dynamic",
    )
    service = EvidenceService(db, embedder, relevance_threshold=0.72)
    assert service.find_evidence_for_opportunity(opportunity) is None


def test_returns_none_when_nothing_clears_the_threshold(db):
    """The core 'never fabricate a citation' behavior — an unrelated
    opportunity should get no evidence, not the closest available one."""
    from app.models import AIOpportunity, AutomationPotential, HumanAIResponsibility

    embedder = FakeEmbeddingProvider()
    _make_research_source(
        db, embedder,
        title="Completely Unrelated Topic About Gardening",
        summary="Not about banking or AI at all.",
    )
    opportunity = AIOpportunity(
        id=uuid.uuid4(), name="AI Credit Risk Scoring", description="",
        automation_potential=AutomationPotential.HIGH,
        human_ai_responsibility=HumanAIResponsibility.AI_AUTOMATES, source="dynamic",
    )
    service = EvidenceService(db, embedder, relevance_threshold=0.72)
    assert service.find_evidence_for_opportunity(opportunity) is None


# ----------------------------------------------------------------------
# Full pipeline integration: evidence attaches when a relevant source exists
# ----------------------------------------------------------------------

def test_pipeline_attaches_evidence_when_relevant_source_exists(db, value_chain):
    embedder_for_seed = FakeEmbeddingProvider()
    # The opportunity in _valid_extraction_payload() is named
    # "Automated Document Extraction" with description "Extract structured
    # data from loan documents automatically." — EvidenceService queries
    # with f"{name}. {description}", so the research source must be
    # embedded with that SAME combined text for the fake (hash-based)
    # embedder to treat them as matching. A real semantic model wouldn't
    # need this exact alignment, but the fake one has no notion of
    # near-equality — see FakeEmbeddingProvider's docstring.
    opportunity_query_text = (
        "Automated Document Extraction. "
        "Extract structured data from documents automatically."
    )
    _make_research_source(
        db, embedder_for_seed,
        title="Automated Document Extraction",
        summary="Test research source about automated document extraction in lending.",
        embed_text=opportunity_query_text,
    )

    payload = _valid_extraction_payload()
    llm = ScriptedLLMProvider(payload)
    pipeline = ProcessAnalysisPipeline(
        db=db, llm_provider=llm, embedding_provider=FakeEmbeddingProvider(),
        entity_similarity_threshold=0.86, evidence_relevance_threshold=0.86,
    )
    job = pipeline.run("Warehouse Inventory Forecasting", value_chain.id)

    assert job.status.value == "completed"
    evidence_rows = db.query(Evidence).all()
    assert len(evidence_rows) == 1
    assert evidence_rows[0].research_source.title == "Automated Document Extraction"


def test_pipeline_succeeds_with_no_evidence_when_corpus_is_empty(db, value_chain):
    """The common case before scripts/seed_research_sources.py has been
    run — the job must still complete cleanly with zero Evidence rows."""
    payload = _valid_extraction_payload()
    llm = ScriptedLLMProvider(payload)
    pipeline = ProcessAnalysisPipeline(
        db=db, llm_provider=llm, embedding_provider=FakeEmbeddingProvider(),
        entity_similarity_threshold=0.86,
    )
    job = pipeline.run("Warehouse Inventory Forecasting", value_chain.id)

    assert job.status.value == "completed"
    assert db.query(Evidence).count() == 0


# ----------------------------------------------------------------------
# source parameter: seed vs dynamic provenance
# ----------------------------------------------------------------------

def test_default_source_is_dynamic(db, value_chain):
    from app.models import Process, Role

    payload = _valid_extraction_payload()
    llm = ScriptedLLMProvider(payload)
    pipeline = ProcessAnalysisPipeline(
        db=db, llm_provider=llm, embedding_provider=FakeEmbeddingProvider(),
        entity_similarity_threshold=0.86,
    )
    job = pipeline.run("Warehouse Inventory Forecasting", value_chain.id)

    process = db.get(Process, job.result_entity_id)
    assert process.source == "dynamic"
    assert process.activities[0].roles[0].source == "dynamic"


def test_explicit_seed_source_is_applied_to_all_new_entities(db, value_chain):
    from app.models import AIOpportunity, Process, Role, Skill

    payload = _valid_extraction_payload()
    llm = ScriptedLLMProvider(payload)
    pipeline = ProcessAnalysisPipeline(
        db=db, llm_provider=llm, embedding_provider=FakeEmbeddingProvider(),
        entity_similarity_threshold=0.86,
    )
    job = pipeline.run("Warehouse Inventory Forecasting", value_chain.id, source="seed")

    assert job.status.value == "completed"
    process = db.get(Process, job.result_entity_id)
    assert process.source == "seed"
    activity = process.activities[0]
    assert activity.source == "seed"
    role = activity.roles[0]
    assert role.source == "seed"
    assert role.skills[0].source == "seed"
    assert activity.ai_opportunities[0].source == "seed"


def test_seed_run_still_reuses_existing_entities_via_dedup(db, value_chain):
    """Provenance labeling must not interfere with dedup — a seed run
    reusing a role/skill created by an earlier dynamic run should NOT
    overwrite that role's existing source."""
    from app.models import Role

    payload_1 = _valid_extraction_payload(role_title="Credit Analyst", skill_name="Credit Risk Assessment")
    pipeline_1 = ProcessAnalysisPipeline(
        db=db, llm_provider=ScriptedLLMProvider(payload_1), embedding_provider=FakeEmbeddingProvider(),
        entity_similarity_threshold=0.86,
    )
    pipeline_1.run("Loan Underwriting", value_chain.id, source="dynamic")

    payload_2 = _valid_extraction_payload(
        process_purpose="Second process.", role_title="Credit Analyst", skill_name="Credit Risk Assessment",
    )
    pipeline_2 = ProcessAnalysisPipeline(
        db=db, llm_provider=ScriptedLLMProvider(payload_2), embedding_provider=FakeEmbeddingProvider(),
        entity_similarity_threshold=0.86,
    )
    pipeline_2.run("Loan Portfolio Monitoring", value_chain.id, source="seed")

    roles = db.query(Role).filter(Role.title == "Credit Analyst").all()
    assert len(roles) == 1  # still deduped correctly
    assert roles[0].source == "dynamic"  # unchanged — first run's provenance wins, not overwritten
