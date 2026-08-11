"""
GraphEdge.

Deliberately denormalized. Every other relationship in this schema (see
value_chain.py, role_skill.py, ai_opportunity.py) is a typed, foreign-keyed
junction table — that's where integrity lives. GraphEdge is a *read-optimized
mirror* of those same relationships, written by a service-layer sync step
whenever a relationship changes, purely so GET /api/graph/{type}/{id} can
return everything React Flow needs in one indexed query instead of joining
five junction tables on every graph render.

This is the "why not just use a graph database" answer made concrete: this
table gives graph-shaped reads without giving up relational integrity
anywhere else.
"""
import enum
import uuid

from sqlalchemy import Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPKMixin, pg_enum


class GraphNodeType(str, enum.Enum):
    PROCESS = "process"
    ACTIVITY = "activity"
    ROLE = "role"
    SKILL = "skill"
    AI_OPPORTUNITY = "ai_opportunity"


class GraphEdge(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "graph_edges"

    source_type: Mapped[GraphNodeType] = mapped_column(pg_enum(GraphNodeType, "graph_node_type"))
    source_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    target_type: Mapped[GraphNodeType] = mapped_column(pg_enum(GraphNodeType, "graph_node_type"))
    target_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    edge_label: Mapped[str] = mapped_column(String(80))
    """e.g. 'contains', 'performed_by', 'requires', 'affected_by'."""

    __table_args__ = (
        Index("ix_graph_edges_source", "source_type", "source_id"),
        Index("ix_graph_edges_target", "target_type", "target_id"),
    )
