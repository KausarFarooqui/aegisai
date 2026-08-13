"""
GET /api/processes, GET /api/processes/{id}, GET /api/value-chains — backing
the Executive Dashboard's process list, the Process Intelligence detail
page, and the value-chain selector on the Analyze New Process form.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models import Process, ValueChain
from app.repositories.entity_repository import ProcessRepository, ValueChainRepository
from app.schemas.process import ProcessDetailOut, ProcessSummaryOut, ValueChainOut

router = APIRouter(tags=["processes"])


@router.get("/api/processes", response_model=list[ProcessSummaryOut])
def list_processes(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> list[Process]:
    return ProcessRepository(db).list(limit=limit, offset=offset)


@router.get("/api/processes/{process_id}", response_model=ProcessDetailOut)
def get_process(process_id: uuid.UUID, db: Session = Depends(get_db)) -> Process:
    process = ProcessRepository(db).get_by_id(process_id)
    if process is None:
        raise HTTPException(status_code=404, detail=f"Process {process_id} not found")
    return process


@router.get("/api/value-chains", response_model=list[ValueChainOut])
def list_value_chains(db: Session = Depends(get_db)) -> list[ValueChain]:
    return ValueChainRepository(db).list(limit=100)
