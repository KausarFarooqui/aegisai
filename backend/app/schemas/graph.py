import uuid

from pydantic import BaseModel


class GraphNodeOut(BaseModel):
    id: uuid.UUID
    type: str
    label: str


class GraphEdgeOut(BaseModel):
    source_id: uuid.UUID
    source_type: str
    target_id: uuid.UUID
    target_type: str
    label: str


class GraphResponse(BaseModel):
    nodes: list[GraphNodeOut]
    edges: list[GraphEdgeOut]
