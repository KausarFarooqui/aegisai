"""
Tests for scripts/seed_processes.py's orchestration logic. Uses the same
fake LLM/embedding providers as the rest of the test suite — network-
independent, proves the script's loop/error-handling/idempotency logic
works correctly, not the quality of real Groq output (that's on you to
confirm by actually running it — see the README).
"""
import sys
from pathlib import Path

import pytest
from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import seed_processes  # noqa: E402

from app.models import Industry, Organization, Process, Role, Skill, ValueChain  # noqa: E402
from tests.test_analysis_pipeline import FakeEmbeddingProvider, ScriptedLLMProvider, _valid_extraction_payload  # noqa: E402


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


def test_get_or_create_org_structure_creates_industry_org_and_both_value_chains(db):
    value_chains = seed_processes._get_or_create_org_structure(db)

    assert set(value_chains.keys()) == {"Retail Lending", "Trade Finance & Compliance"}
    assert db.query(Industry).filter(Industry.name == seed_processes.INDUSTRY_NAME).count() == 1
    assert db.query(Organization).filter(Organization.name == seed_processes.ORGANIZATION_NAME).count() == 1
    assert db.query(ValueChain).count() == 2


def test_get_or_create_org_structure_is_idempotent(db):
    first = seed_processes._get_or_create_org_structure(db)
    second = seed_processes._get_or_create_org_structure(db)

    assert first["Retail Lending"].id == second["Retail Lending"].id
    assert first["Trade Finance & Compliance"].id == second["Trade Finance & Compliance"].id
    assert db.query(Industry).count() == 1
    assert db.query(Organization).count() == 1
    assert db.query(ValueChain).count() == 2


def test_seed_plan_covers_the_agreed_scope():
    """Locks in the scoped-down target from the architecture doc: ~10
    processes across exactly two value chains — catches an accidental
    scope change (someone adding an 11th process, or a typo'd value
    chain name) before it silently drifts from what was agreed."""
    total_processes = sum(len(processes) for _, _, processes in seed_processes.SEED_PLAN)
    value_chain_names = {name for name, _, _ in seed_processes.SEED_PLAN}

    assert total_processes == 10
    assert value_chain_names == {"Retail Lending", "Trade Finance & Compliance"}
    # Every process name is globally unique — a duplicate here would make
    # the second occurrence silently skip during a real run
    all_names = [p for _, _, procs in seed_processes.SEED_PLAN for p, _ in procs]
    assert len(all_names) == len(set(all_names))


def test_full_seed_run_completes_all_ten_processes(db, monkeypatch):
    """Runs the actual seed script's main() against all 10 real process
    names/contexts from SEED_PLAN, with fake providers standing in for
    Groq/sentence-transformers. Every LLM call gets the same scripted
    payload (role/skill names repeat on purpose here — that's what proves
    dedup fires correctly across a real 10-process seed run, not just a
    2-process toy example)."""
    llm = ScriptedLLMProvider(_valid_extraction_payload())
    embeddings = FakeEmbeddingProvider()

    results = seed_processes.main(llm=llm, embeddings=embeddings)

    assert len(results["seeded"]) == 10
    assert len(results["skipped_existing"]) == 0
    assert len(results["failed"]) == 0
    assert db.query(Process).count() == 10

    # Same role/skill names proposed for every process -> dedup should
    # collapse them to ONE shared Role/Skill, not ten separate ones
    assert db.query(Role).filter(Role.title == "Credit Analyst").count() == 1
    assert db.query(Skill).filter(Skill.name == "Credit Risk Assessment").count() == 1


def test_rerunning_seed_script_skips_all_existing_processes(db):
    """The 'safe to re-run' claim in the script's own docstring, verified:
    a second full run against an already-seeded database should create
    nothing new."""
    llm = ScriptedLLMProvider(_valid_extraction_payload())
    embeddings = FakeEmbeddingProvider()

    first_run = seed_processes.main(llm=llm, embeddings=embeddings)
    assert len(first_run["seeded"]) == 10

    second_run = seed_processes.main(llm=llm, embeddings=embeddings)
    assert len(second_run["seeded"]) == 0
    assert len(second_run["skipped_existing"]) == 10
    assert len(second_run["failed"]) == 0
    assert db.query(Process).count() == 10  # unchanged


def test_seeded_processes_are_tagged_with_seed_provenance(db):
    llm = ScriptedLLMProvider(_valid_extraction_payload())
    embeddings = FakeEmbeddingProvider()
    seed_processes.main(llm=llm, embeddings=embeddings)

    processes = db.query(Process).all()
    assert all(p.source == "seed" for p in processes)
