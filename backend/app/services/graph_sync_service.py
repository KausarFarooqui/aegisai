"""
GraphSyncService.

Thin wrapper around GraphEdgeRepository that the analysis pipeline calls
once it knows the final set of relationships for a newly analyzed Process.
Kept as its own service (rather than folded into the pipeline directly) so
the same sync logic can be reused by the seed script and by Role/Skill/
AIOpportunity analysis entry points later, without duplicating edge-writing
code in each.
"""
import uuid

from sqlalchemy.orm import Session

from app.models import GraphNodeType
from app.repositories.graph_repository import GraphEdgeRepository


class GraphSyncService:
    def __init__(self, db: Session):
        self.edges = GraphEdgeRepository(db)

    def sync_process_activity(self, process_id: uuid.UUID, activity_id: uuid.UUID) -> None:
        self.edges.add_edge(
            GraphNodeType.PROCESS, process_id, GraphNodeType.ACTIVITY, activity_id, "contains"
        )

    def sync_activity_role(self, activity_id: uuid.UUID, role_id: uuid.UUID) -> None:
        self.edges.add_edge(
            GraphNodeType.ACTIVITY, activity_id, GraphNodeType.ROLE, role_id, "performed_by"
        )

    def sync_role_skill(self, role_id: uuid.UUID, skill_id: uuid.UUID) -> None:
        self.edges.add_edge(
            GraphNodeType.ROLE, role_id, GraphNodeType.SKILL, skill_id, "requires"
        )

    def sync_activity_ai_opportunity(self, activity_id: uuid.UUID, opportunity_id: uuid.UUID) -> None:
        self.edges.add_edge(
            GraphNodeType.ACTIVITY, activity_id, GraphNodeType.AI_OPPORTUNITY, opportunity_id,
            "affected_by",
        )

    def sync_ai_opportunity_role(self, opportunity_id: uuid.UUID, role_id: uuid.UUID) -> None:
        self.edges.add_edge(
            GraphNodeType.AI_OPPORTUNITY, opportunity_id, GraphNodeType.ROLE, role_id, "impacts"
        )

    def sync_ai_opportunity_skill(self, opportunity_id: uuid.UUID, skill_id: uuid.UUID) -> None:
        self.edges.add_edge(
            GraphNodeType.AI_OPPORTUNITY, opportunity_id, GraphNodeType.SKILL, skill_id, "changes"
        )
