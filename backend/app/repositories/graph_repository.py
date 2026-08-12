"""
GraphEdgeRepository — the read/write layer for the denormalized graph_edges
table. See app/models/graph_edge.py for why this table exists alongside
the typed junction tables.
"""
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import GraphEdge, GraphNodeType
from app.repositories.base import BaseRepository


class GraphEdgeRepository(BaseRepository[GraphEdge]):
    def __init__(self, db: Session):
        super().__init__(db, GraphEdge)

    def add_edge(
        self,
        source_type: GraphNodeType,
        source_id: uuid.UUID,
        target_type: GraphNodeType,
        target_id: uuid.UUID,
        edge_label: str,
    ) -> GraphEdge:
        """
        Idempotent — checks for an existing identical edge before inserting,
        so re-running analysis on an entity that already has some edges
        (e.g. a Role matched via dedup that already appears elsewhere in
        the graph) doesn't create duplicate rows.
        """
        existing = self.db.scalars(
            select(GraphEdge).where(
                GraphEdge.source_type == source_type,
                GraphEdge.source_id == source_id,
                GraphEdge.target_type == target_type,
                GraphEdge.target_id == target_id,
                GraphEdge.edge_label == edge_label,
            )
        ).first()
        if existing:
            return existing
        edge = GraphEdge(
            source_type=source_type, source_id=source_id,
            target_type=target_type, target_id=target_id,
            edge_label=edge_label,
        )
        self.db.add(edge)
        return edge

    def get_edges_for_node(self, node_type: GraphNodeType, node_id: uuid.UUID) -> list[GraphEdge]:
        """All edges where this node is either the source or the target —
        what the graph visualization endpoint needs to render one node's
        immediate neighborhood."""
        stmt = select(GraphEdge).where(
            ((GraphEdge.source_type == node_type) & (GraphEdge.source_id == node_id))
            | ((GraphEdge.target_type == node_type) & (GraphEdge.target_id == node_id))
        )
        return list(self.db.scalars(stmt).all())
