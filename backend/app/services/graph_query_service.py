"""
GraphQueryService — BFS traversal over graph_edges backing
GET /api/graph/process/{id}.

Scalability note: this does one query per BFS layer (a handful of queries
for a typical process's neighborhood — Process->Activity->Role->Skill is
only 3-4 hops). At far larger scale, this would become a single recursive
CTE query over graph_edges, or a precomputed adjacency cache refreshed by
graph_sync_service.py — not built now because it isn't needed at seed-data
scale and would add complexity with no visible benefit yet, but this is
the concrete answer to "what changes at 10,000 processes" for this
specific endpoint.
"""
import uuid

from sqlalchemy.orm import Session

from app.models import AIOpportunity, Activity, GraphNodeType, Process, Role, Skill
from app.repositories.graph_repository import GraphEdgeRepository
from app.schemas.graph import GraphEdgeOut, GraphNodeOut, GraphResponse

_NODE_MODEL_MAP: dict[GraphNodeType, tuple[type, str]] = {
    GraphNodeType.PROCESS: (Process, "name"),
    GraphNodeType.ACTIVITY: (Activity, "name"),
    GraphNodeType.ROLE: (Role, "title"),
    GraphNodeType.SKILL: (Skill, "name"),
    GraphNodeType.AI_OPPORTUNITY: (AIOpportunity, "name"),
}


class GraphQueryService:
    def __init__(self, db: Session):
        self.db = db
        self.edges = GraphEdgeRepository(db)

    def get_neighborhood(
        self, start_type: GraphNodeType, start_id: uuid.UUID, max_hops: int = 4
    ) -> GraphResponse:
        visited_nodes: set[tuple[GraphNodeType, uuid.UUID]] = {(start_type, start_id)}
        visited_edge_keys: set[tuple] = set()
        collected_edges = []

        frontier = [(start_type, start_id)]
        for _ in range(max_hops):
            if not frontier:
                break
            next_frontier = []
            for node_type, node_id in frontier:
                for edge in self.edges.get_edges_for_node(node_type, node_id):
                    key = (edge.source_type, edge.source_id, edge.target_type, edge.target_id, edge.edge_label)
                    if key not in visited_edge_keys:
                        visited_edge_keys.add(key)
                        collected_edges.append(edge)
                    for neighbor in ((edge.source_type, edge.source_id), (edge.target_type, edge.target_id)):
                        if neighbor not in visited_nodes:
                            visited_nodes.add(neighbor)
                            next_frontier.append(neighbor)
            frontier = next_frontier

        nodes = [
            GraphNodeOut(id=node_id, type=node_type.value, label=self._resolve_label(node_type, node_id))
            for node_type, node_id in visited_nodes
        ]
        edges = [
            GraphEdgeOut(
                source_id=e.source_id, source_type=e.source_type.value,
                target_id=e.target_id, target_type=e.target_type.value,
                label=e.edge_label,
            )
            for e in collected_edges
        ]
        return GraphResponse(nodes=nodes, edges=edges)

    def _resolve_label(self, node_type: GraphNodeType, node_id: uuid.UUID) -> str:
        model, attr = _NODE_MODEL_MAP[node_type]
        entity = self.db.get(model, node_id)
        return getattr(entity, attr) if entity is not None else "(deleted)"
