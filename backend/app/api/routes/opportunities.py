"""
GET /api/opportunities — backing the AI Opportunities browse page. Added
alongside the frontend build after noticing processes/roles/skills/graph
all had list endpoints but AI opportunities never did, even though it's
one of the 8 required pages in the MODUS brief.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models import AIOpportunity
from app.repositories.entity_repository import AIOpportunityRepository
from app.schemas.process import AIOpportunityOut

router = APIRouter(tags=["opportunities"])


@router.get("/api/opportunities", response_model=list[AIOpportunityOut])
def list_opportunities(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> list[AIOpportunity]:
    return AIOpportunityRepository(db).list(limit=limit, offset=offset)
