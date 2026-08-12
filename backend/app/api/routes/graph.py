"""
GET /api/graph/{node_type}/{node_id} — backing the Intelligence Graph page.
One generic endpoint rather than separate /api/graph/process/{id},
/api/graph/role/{id}, etc. — the traversal logic (GraphQueryService) is
identical regardless of the starting node type, so a single parameterized
route avoids duplicating four near-identical handlers.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models import GraphNodeType
from app.schemas.graph import GraphResponse
from app.services.graph_query_service import GraphQueryService

router = APIRouter(tags=["graph"])


@router.get("/api/graph/{node_type}/{node_id}", response_model=GraphResponse)
def get_graph_neighborhood(
    node_type: str,
    node_id: uuid.UUID,
    max_hops: int = Query(4, ge=1, le=8),
    db: Session = Depends(get_db),
) -> GraphResponse:
    try:
        node_type_enum = GraphNodeType(node_type.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid node_type '{node_type}' — expected one of {[e.value for e in GraphNodeType]}",
        )
    return GraphQueryService(db).get_neighborhood(node_type_enum, node_id, max_hops=max_hops)
