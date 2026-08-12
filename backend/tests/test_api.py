"""
API-level tests — exercises the actual HTTP layer (FastAPI TestClient),
not just the pipeline/service classes directly. Uses dependency overrides
to inject the fake LLM/embedding providers from test_analysis_pipeline.py
and a real Postgres session, so these tests prove the routes, request/
response schemas, and status codes are correct without needing a live
Groq call.
"""
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.api.deps import get_db, get_embeddings, get_llm
from app.main import app
from app.models import Industry, ValueChain
from tests.test_analysis_pipeline import FakeEmbeddingProvider, ScriptedLLMProvider, _valid_extraction_payload


@pytest.fixture(autouse=True)
def _clean_tables(db):
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


@pytest.fixture()
def client(db):
    """
    Overrides get_db to reuse the test's own session (so assertions in the
    test can see what the request created, in the same transaction/
    connection) and overrides the LLM/embedding providers with the same
    fakes the pipeline tests use — no network calls anywhere in this file.
    """
    def _override_get_db():
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_llm] = lambda: ScriptedLLMProvider(_valid_extraction_payload())
    app.dependency_overrides[get_embeddings] = lambda: FakeEmbeddingProvider()

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture()
def value_chain(db) -> ValueChain:
    industry = Industry(name=f"Test Banking {uuid.uuid4()}")
    vc = ValueChain(name=f"Test Retail Lending {uuid.uuid4()}", industry=industry, sequence_order=1)
    db.add_all([industry, vc])
    db.commit()
    return vc


def test_health_check_reports_database_connected(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["database_connected"] is True


def test_dashboard_reflects_empty_state(client):
    resp = client.get("/api/dashboard")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_processes"] == 0
    assert body["most_affected_roles"] == []


def test_analyze_endpoint_runs_the_real_pipeline_and_returns_completed_job(client, value_chain):
    resp = client.post(
        "/api/processes/analyze",
        json={
            "process_name": "Warehouse Inventory Forecasting",
            "value_chain_id": str(value_chain.id),
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "completed"
    assert body["result_entity_id"] is not None
    assert body["error_message"] is None


def test_analyze_endpoint_returns_failed_status_not_500_for_duplicate_process(client, value_chain):
    """A cleanly-failed pipeline run is a valid 200 response with
    status=failed — not a server error. This is what lets a judge see
    'validation caught this' in the UI instead of a stack trace."""
    first = client.post(
        "/api/processes/analyze",
        json={"process_name": "Loan Underwriting", "value_chain_id": str(value_chain.id)},
    )
    assert first.json()["status"] == "completed"

    second = client.post(
        "/api/processes/analyze",
        json={"process_name": "Loan Underwriting", "value_chain_id": str(value_chain.id)},
    )
    assert second.status_code == 200
    assert second.json()["status"] == "failed"
    assert "already exists" in second.json()["error_message"]


def test_analyze_then_fetch_process_detail_shows_full_connected_graph(client, value_chain):
    analyze_resp = client.post(
        "/api/processes/analyze",
        json={"process_name": "Warehouse Inventory Forecasting", "value_chain_id": str(value_chain.id)},
    )
    process_id = analyze_resp.json()["result_entity_id"]

    detail_resp = client.get(f"/api/processes/{process_id}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["name"] == "Warehouse Inventory Forecasting"
    assert len(detail["activities"]) == 1
    assert detail["activities"][0]["roles"][0]["title"] == "Credit Analyst"
    assert detail["activities"][0]["ai_opportunities"][0]["assessment"]["total_score"] == pytest.approx(84.45)


def test_get_process_404_for_unknown_id(client):
    resp = client.get(f"/api/processes/{uuid.uuid4()}")
    assert resp.status_code == 404


def test_get_analysis_job_by_id(client, value_chain):
    analyze_resp = client.post(
        "/api/processes/analyze",
        json={"process_name": "Warehouse Inventory Forecasting", "value_chain_id": str(value_chain.id)},
    )
    job_id = analyze_resp.json()["id"]

    job_resp = client.get(f"/api/analysis/{job_id}")
    assert job_resp.status_code == 200
    assert job_resp.json()["status"] == "completed"
    assert len(job_resp.json()["stage_log"]) == 6


def test_graph_endpoint_returns_connected_nodes_and_edges(client, value_chain):
    analyze_resp = client.post(
        "/api/processes/analyze",
        json={"process_name": "Warehouse Inventory Forecasting", "value_chain_id": str(value_chain.id)},
    )
    process_id = analyze_resp.json()["result_entity_id"]

    graph_resp = client.get(f"/api/graph/process/{process_id}")
    assert graph_resp.status_code == 200
    body = graph_resp.json()
    node_types = {n["type"] for n in body["nodes"]}
    assert node_types == {"process", "activity", "role", "skill", "ai_opportunity"}
    assert len(body["edges"]) == 6  # matches test_graph_edges_created_for_every_relationship


def test_invalid_graph_node_type_returns_400(client):
    resp = client.get(f"/api/graph/not_a_real_type/{uuid.uuid4()}")
    assert resp.status_code == 400


def test_skills_filter_by_trend(client, value_chain):
    client.post(
        "/api/processes/analyze",
        json={"process_name": "Warehouse Inventory Forecasting", "value_chain_id": str(value_chain.id)},
    )
    resp = client.get("/api/skills", params={"trend": "declining"})
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["name"] == "Credit Risk Assessment"


def test_skills_filter_rejects_invalid_trend_value(client):
    resp = client.get("/api/skills", params={"trend": "not_a_real_trend"})
    assert resp.status_code == 400
