import type { GraphEdgeOut, GraphNodeOut } from "@/api/types";

export interface PositionedNode extends GraphNodeOut {
  x: number;
  y: number;
}

const LAYER_SPACING = 260;
const NODE_SPACING = 90;

/**
 * Positions nodes by BFS distance from the root (the node the graph was
 * fetched around) into left-to-right layers, with light deterministic
 * jitter so it reads as a constellation rather than a rigid grid. No
 * layout library dependency — this graph is small enough (dozens, not
 * thousands, of nodes at seed-data scale) that a simple BFS layering is
 * both sufficient and easy to reason about, versus pulling in dagre for
 * a fuller DAG layout. Revisit if node counts grow enough that layers
 * start overlapping badly — see decision log scalability notes.
 */
export function layoutGraph(
  nodes: GraphNodeOut[],
  edges: GraphEdgeOut[],
  rootId: string,
): PositionedNode[] {
  const adjacency = new Map<string, Set<string>>();
  for (const node of nodes) adjacency.set(node.id, new Set());
  for (const edge of edges) {
    adjacency.get(edge.source_id)?.add(edge.target_id);
    adjacency.get(edge.target_id)?.add(edge.source_id);
  }

  const layerOf = new Map<string, number>();
  const queue: string[] = [rootId];
  layerOf.set(rootId, 0);
  while (queue.length) {
    const current = queue.shift()!;
    const currentLayer = layerOf.get(current)!;
    for (const neighbor of adjacency.get(current) ?? []) {
      if (!layerOf.has(neighbor)) {
        layerOf.set(neighbor, currentLayer + 1);
        queue.push(neighbor);
      }
    }
  }

  // Any node not reached from root (shouldn't happen given the backend
  // always returns a connected neighborhood) still gets placed, not lost.
  let maxLayer = Math.max(0, ...layerOf.values());
  for (const node of nodes) {
    if (!layerOf.has(node.id)) layerOf.set(node.id, ++maxLayer);
  }

  const nodesByLayer = new Map<number, GraphNodeOut[]>();
  for (const node of nodes) {
    const layer = layerOf.get(node.id)!;
    if (!nodesByLayer.has(layer)) nodesByLayer.set(layer, []);
    nodesByLayer.get(layer)!.push(node);
  }

  const positioned: PositionedNode[] = [];
  for (const [layer, layerNodes] of nodesByLayer) {
    const totalHeight = (layerNodes.length - 1) * NODE_SPACING;
    layerNodes.forEach((node, i) => {
      const seed = hashString(node.id);
      const jitterX = ((seed % 40) - 20) * 0.6;
      const jitterY = (((seed >> 4) % 30) - 15) * 0.6;
      positioned.push({
        ...node,
        x: layer * LAYER_SPACING + jitterX,
        y: i * NODE_SPACING - totalHeight / 2 + jitterY,
      });
    });
  }

  return positioned;
}

function hashString(s: string): number {
  let h = 0;
  for (let i = 0; i < s.length; i++) {
    h = (h << 5) - h + s.charCodeAt(i);
    h |= 0;
  }
  return Math.abs(h);
}
