"""
POST /api/processes/analyze — the HTTP entry point for the Surprise Record
Test. This is deliberately thin: it constructs a ProcessAnalysisPipeline
with the request-scoped DB session and the configured LLM/embedding
providers, and returns whatever AnalysisJob comes back — success or
failure both return 200 with the job's real status, since "the pipeline
ran and failed cleanly" is a valid, informative outcome, not a server
error. A 500 here would mean something actually unexpected happened.

GET /api/analysis/{job_id} lets the frontend poll job status while the
pipeline runs, per the async design in the architecture doc.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_db, get_embeddings, get_llm
from app.config.settings import get_settings
from app.intelligence.embeddings import EmbeddingProvider
from app.intelligence.llm_provider import LLMProvider
from app.models import AnalysisJob
from app.schemas.analysis import AnalysisJobOut, AnalyzeProcessRequest
from app.workers.analysis_pipeline import ProcessAnalysisPipeline
from sqlalchemy.orm import Session

router = APIRouter(tags=["analyze"])


@router.post("/api/processes/analyze", response_model=AnalysisJobOut)
def analyze_process(
    request: AnalyzeProcessRequest,
    db: Session = Depends(get_db),
    llm: LLMProvider = Depends(get_llm),
    embeddings: EmbeddingProvider = Depends(get_embeddings),
) -> AnalysisJob:
    settings = get_settings()
    pipeline = ProcessAnalysisPipeline(
        db=db,
        llm_provider=llm,
        embedding_provider=embeddings,
        entity_similarity_threshold=settings.entity_similarity_threshold,
        evidence_relevance_threshold=settings.evidence_relevance_threshold,
    )
    job = pipeline.run(
        process_name=request.process_name,
        value_chain_id=request.value_chain_id,
        process_context=request.process_context,
    )
    return job


@router.get("/api/analysis/{job_id}", response_model=AnalysisJobOut)
def get_analysis_job(job_id: uuid.UUID, db: Session = Depends(get_db)) -> AnalysisJob:
    job = db.get(AnalysisJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"AnalysisJob {job_id} not found")
    return job
