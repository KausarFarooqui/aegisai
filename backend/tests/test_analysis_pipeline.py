"""
End-to-end tests for ProcessAnalysisPipeline — the actual Surprise Record
Test mechanism — run against a REAL Postgres database (the `db` fixture
from conftest.py), with a fake LLM provider (network-independent, same
pattern as test_llm_provider.py) and a fake but deterministic embedding
provider (network-independent, since the real model lives on
huggingface.co which isn't reachable from this sandbox — the real model's
semantic quality was proven separately in Phase 4, on real infrastructure;
what's being proven here is that the PIPELINE WIRING is correct).

The fake embedder hashes normalized text into a deterministic unit vector:
identical (case/whitespace-insensitive) text always produces an identical
vector (similarity 1.0 — trivially matches for dedup), and different text
produces effectively orthogonal vectors (near-zero similarity — trivially
doesn't match). This is sufficient to prove the dedup MECHANISM fires
correctly; the fine-grained "how similar is similar enough" question is
what Phase 4's real-model verification already answered.
"""
import hashlib
import json
import uuid

import numpy as np
import pytest
from sqlalchemy import text

from app.intelligence.llm_provider import LLMProvider
from app.models import (
    AnalysisJobStatus,
    HumanAIResponsibility,
    ImpactBand,
    Industry,
    Role,
    Skill,
    SkillTrend,
    ValueChain,
)
from app.workers.analysis_pipeline import ProcessAnalysisPipeline


@pytest.fixture(autouse=True)
def _clean_tables(db):
    """
    The pipeline deliberately commits mid-flight (job status must be
    visible in real time, per app/workers/analysis_pipeline.py's design) —
    which means the default `db` fixture's teardown-time `rollback()`
    alone isn't enough to isolate tests from each other, since committed
    data survives a rollback. Truncate everything these tests touch before
    each test runs, so every test starts from a genuinely clean slate
    regardless of commit behavior in previous tests.
    """
    tables = [
        "graph_edges", "evidence", "future_responsibilities", "ai_assessments",
        "activity_ai_opportunities", "ai_opportunity_role_impacts",
        "ai_opportunity_skill_impacts", "ai_opportunities", "activity_roles",
        "role_skills", "activities", "processes", "roles", "skills",
        "value_chains", "organizations", "industries", "analysis_jobs",
    ]
    for t in tables:
        db.execute(text(f"TRUNCATE TABLE {t} CASCADE"))
    db.commit()
    yield


class FakeEmbeddingProvider:
    """Deterministic, network-independent stand-in for the real
    sentence-transformers model — see module docstring."""

    def __init__(self, dimensions: int = 384):
        self.dimensions = dimensions
        self.model_name = "fake-test-embedder"

    def encode(self, text: str) -> list[float]:
        normalized = text.strip().lower()
        seed = int(hashlib.sha256(normalized.encode()).hexdigest()[:16], 16) % (2**32)
        rng = np.random.default_rng(seed)
        vec = rng.normal(0, 1, self.dimensions)
        vec = vec / np.linalg.norm(vec)
        return vec.tolist()

    def encode_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.encode(t) for t in texts]


class ScriptedLLMProvider(LLMProvider):
    """Returns a pre-scripted JSON response regardless of prompt content —
    lets tests control exactly what the pipeline receives without a real
    LLM call."""

    name = "scripted-test-llm"

    def __init__(self, response_payload: dict):
        self.response_payload = response_payload
        self.call_count = 0

    def _raw_complete(self, system_prompt: str, user_prompt: str) -> str:
        self.call_count += 1
        return json.dumps(self.response_payload)


def _valid_extraction_payload(
    process_purpose: str = "Assess creditworthiness of loan applicants.",
    role_title: str = "Credit Analyst",
    skill_name: str = "Credit Risk Assessment",
) -> dict:
    return {
        "business_purpose": process_purpose,
        "current_challenges": "Manual review is slow.",
        "activities": [
            {
                "name": "Review financial statements",
                "description": "Manual document review.",
                "performed_by_role_titles": [role_title],
            }
        ],
        "roles": [
            {"title": role_title, "is_new": True, "requires_skill_names": [skill_name]}
        ],
        "skills": [{"name": skill_name, "category": "analytical", "is_new": True}],
        "ai_opportunities": [
            {
                "name": "Automated Document Extraction",
                "description": "Extract structured data from documents automatically.",
                "automation_potential": "high",
                "human_ai_responsibility": "ai_automates",
                "business_benefit": "Faster processing.",
                "risks": "Extraction errors on edge cases.",
                "affected_activity_names": ["Review financial statements"],
                "factor_repetitiveness": {"value": 90, "reason": "Routine daily task."},
                "factor_data_availability": {"value": 85, "reason": "Documents are digitized."},
                "factor_predictability": {"value": 80, "reason": "Consistent structure."},
                "factor_digitalization": {"value": 75, "reason": "Already mostly digital."},
                "factor_ai_capability_fit": {"value": 88, "reason": "Mature AI capability."},
            }
        ],
    }


@pytest.fixture()
def value_chain(db) -> ValueChain:
    industry = Industry(name=f"Test Banking {uuid.uuid4()}")
    vc = ValueChain(name=f"Test Retail Lending {uuid.uuid4()}", industry=industry, sequence_order=1)
    db.add_all([industry, vc])
    db.commit()
    return vc


def _make_pipeline(db, response_payload: dict) -> tuple[ProcessAnalysisPipeline, ScriptedLLMProvider]:
    llm = ScriptedLLMProvider(response_payload)
    embeddings = FakeEmbeddingProvider()
    pipeline = ProcessAnalysisPipeline(
        db=db, llm_provider=llm, embedding_provider=embeddings, entity_similarity_threshold=0.86
    )
    return pipeline, llm


# ----------------------------------------------------------------------
# Happy path: the actual Surprise Record Test, end to end
# ----------------------------------------------------------------------

def test_full_pipeline_creates_complete_connected_graph(db, value_chain):
    payload = _valid_extraction_payload()
    pipeline, llm = _make_pipeline(db, payload)

    job = pipeline.run(
        process_name="Warehouse Inventory Forecasting",  # an unseen input, per the MODUS example
        value_chain_id=value_chain.id,
    )

    assert job.status == AnalysisJobStatus.COMPLETED
    assert job.error_message is None
    assert job.result_entity_id is not None
    assert job.duration_ms is not None and job.duration_ms >= 0
    assert llm.call_count == 1

    # Full stage log recorded, in order
    stages = [s["stage"] for s in job.stage_log]
    assert stages == [
        "llm_extraction", "dedup_matching", "scoring", "persistence",
        "evidence_retrieval", "skill_trend_update", "graph_sync",
    ]

    from app.models import Process
    process = db.get(Process, job.result_entity_id)
    assert process.name == "Warehouse Inventory Forecasting"
    assert process.source == "dynamic"
    assert len(process.activities) == 1

    activity = process.activities[0]
    assert activity.name == "Review financial statements"
    assert len(activity.roles) == 1
    assert activity.roles[0].title == "Credit Analyst"
    assert activity.roles[0].source == "dynamic"
    assert activity.roles[0].embedding is not None

    role = activity.roles[0]
    assert len(role.skills) == 1
    assert role.skills[0].name == "Credit Risk Assessment"

    assert len(activity.ai_opportunities) == 1
    opportunity = activity.ai_opportunities[0]
    assert opportunity.automation_potential.value == "high"
    assert opportunity.human_ai_responsibility == HumanAIResponsibility.AI_AUTOMATES
    assert role in opportunity.affected_roles
    assert role.skills[0] in opportunity.affected_skills

    # Deterministic score, not LLM-invented — matches the weighted formula exactly
    expected_score = round(0.30 * 90 + 0.20 * 85 + 0.20 * 80 + 0.15 * 75 + 0.15 * 88, 2)
    assert opportunity.assessment.total_score == expected_score
    assert opportunity.assessment.impact_band == ImpactBand.VERY_HIGH

    # Skill trend was recomputed deterministically from the linked opportunity
    skill = role.skills[0]
    assert skill.trend_classification == SkillTrend.DECLINING  # ai_automates + very_high impact
    assert skill.trend_rationale is not None and "1/1" in skill.trend_rationale


def test_graph_edges_created_for_every_relationship(db, value_chain):
    from app.models import GraphEdge

    payload = _valid_extraction_payload()
    pipeline, _ = _make_pipeline(db, payload)
    job = pipeline.run("Warehouse Inventory Forecasting", value_chain.id)
    assert job.status == AnalysisJobStatus.COMPLETED

    edges = db.query(GraphEdge).all()
    edge_labels = {e.edge_label for e in edges}
    # One edge per relationship type this scenario exercises
    assert edge_labels == {"contains", "performed_by", "requires", "affected_by", "impacts", "changes"}


# ----------------------------------------------------------------------
# Dedup across separate pipeline runs — the actual duplicate-prevention proof
# ----------------------------------------------------------------------

def test_second_run_reuses_identical_role_and_skill_instead_of_duplicating(db, value_chain):
    payload_1 = _valid_extraction_payload(role_title="Credit Analyst", skill_name="Credit Risk Assessment")
    pipeline_1, _ = _make_pipeline(db, payload_1)
    job_1 = pipeline_1.run("Loan Underwriting", value_chain.id)
    assert job_1.status == AnalysisJobStatus.COMPLETED

    # Second, unrelated process, but the LLM proposes the EXACT SAME role/skill names
    payload_2 = _valid_extraction_payload(
        process_purpose="Monitor ongoing loan portfolio risk.",
        role_title="Credit Analyst",
        skill_name="Credit Risk Assessment",
    )
    pipeline_2, _ = _make_pipeline(db, payload_2)
    job_2 = pipeline_2.run("Loan Portfolio Monitoring", value_chain.id)
    assert job_2.status == AnalysisJobStatus.COMPLETED

    all_roles = db.query(Role).filter(Role.title == "Credit Analyst").all()
    all_skills = db.query(Skill).filter(Skill.name == "Credit Risk Assessment").all()

    assert len(all_roles) == 1, "Second run should have REUSED the existing role, not duplicated it"
    assert len(all_skills) == 1, "Second run should have REUSED the existing skill, not duplicated it"

    # Both processes' activities should connect to the SAME role via graph
    # edges — the role also picks up an "impacts" edge from each process's
    # AI opportunity, so we check the specific "performed_by" edge type
    # rather than all edges targeting the role.
    from app.models import GraphEdge, GraphNodeType

    performed_by_edges = db.query(GraphEdge).filter(
        GraphEdge.target_type == GraphNodeType.ROLE,
        GraphEdge.target_id == all_roles[0].id,
        GraphEdge.edge_label == "performed_by",
    ).all()
    assert len(performed_by_edges) == 2, "The shared role should be performed_by an activity in BOTH processes"


def test_second_run_with_genuinely_different_role_creates_a_new_one(db, value_chain):
    payload_1 = _valid_extraction_payload(role_title="Credit Analyst", skill_name="Credit Risk Assessment")
    pipeline_1, _ = _make_pipeline(db, payload_1)
    pipeline_1.run("Loan Underwriting", value_chain.id)

    payload_2 = _valid_extraction_payload(
        process_purpose="Ensure regulatory compliance for trade finance.",
        role_title="Compliance Officer",
        skill_name="Regulatory Reporting",
    )
    pipeline_2, _ = _make_pipeline(db, payload_2)
    job_2 = pipeline_2.run("Trade Finance Compliance Review", value_chain.id)

    assert job_2.status == AnalysisJobStatus.COMPLETED
    assert db.query(Role).count() == 2
    assert db.query(Skill).count() == 2


# ----------------------------------------------------------------------
# Validation and failure handling — must fail cleanly, never fabricate
# ----------------------------------------------------------------------

def test_duplicate_process_name_fails_cleanly_without_creating_entities(db, value_chain):
    payload = _valid_extraction_payload()
    pipeline_1, _ = _make_pipeline(db, payload)
    job_1 = pipeline_1.run("Loan Underwriting", value_chain.id)
    assert job_1.status == AnalysisJobStatus.COMPLETED

    pipeline_2, llm_2 = _make_pipeline(db, payload)
    job_2 = pipeline_2.run("Loan Underwriting", value_chain.id)  # same name again

    assert job_2.status == AnalysisJobStatus.FAILED
    assert "already exists" in job_2.error_message
    assert llm_2.call_count == 0, "Should fail at validation, before ever calling the LLM"

    from app.models import Process
    assert db.query(Process).filter(Process.name == "Loan Underwriting").count() == 1


def test_nonexistent_value_chain_fails_cleanly(db):
    payload = _valid_extraction_payload()
    pipeline, llm = _make_pipeline(db, payload)
    job = pipeline.run("Some New Process", value_chain_id=uuid.uuid4())

    assert job.status == AnalysisJobStatus.FAILED
    assert "does not exist" in job.error_message
    assert llm.call_count == 0


def test_malformed_llm_output_fails_the_job_without_partial_writes(db, value_chain):
    """The LLM returning garbage must never result in partially-created
    entities left behind — the whole point of committing persistence as
    one atomic block."""
    pipeline, llm = _make_pipeline(db, {"not": "the right shape at all"})
    job = pipeline.run("Some New Process", value_chain.id)

    assert job.status == AnalysisJobStatus.FAILED
    assert job.error_message is not None

    from app.models import Process
    assert db.query(Process).count() == 0
    assert db.query(Role).count() == 0
    assert db.query(Skill).count() == 0


def test_llm_referencing_nonexistent_role_in_activity_fails_the_job(db, value_chain):
    payload = _valid_extraction_payload()
    payload["activities"][0]["performed_by_role_titles"] = ["A Role That Was Never Proposed"]
    pipeline, _ = _make_pipeline(db, payload)
    job = pipeline.run("Some New Process", value_chain.id)

    assert job.status == AnalysisJobStatus.FAILED
    assert "not in the roles list" in job.error_message
