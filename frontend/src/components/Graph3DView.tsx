import { useCallback, useEffect, useMemo, useRef } from "react";
import ForceGraph3D, { type ForceGraphMethods, type NodeObject } from "react-force-graph-3d";
import type { GraphNodeType, GraphResponse } from "@/api/types";
import { createNodeObject } from "@/lib/threeConstellation";
import { formatNodeType } from "@/lib/format";

interface Node3D extends NodeObject {
  id: string;
  label: string;
  nodeType: GraphNodeType;
}

export function Graph3DView({
  graph,
  rootId,
  onNodeSelect,
}: {
  graph: GraphResponse;
  rootId: string;
  onNodeSelect: (type: GraphNodeType, id: string) => void;
}) {
  const fgRef = useRef<ForceGraphMethods<Node3D> | undefined>(undefined);

  const graphData = useMemo(
    () => ({
      nodes: graph.nodes.map(
        (n): Node3D => ({ id: n.id, label: n.label, nodeType: n.type }),
      ),
      links: graph.edges.map((e) => ({
        source: e.source_id,
        target: e.target_id,
        label: e.label,
      })),
    }),
    [graph],
  );

  // Gently orbit the camera around the focused node once physics settles —
  // makes the constellation feel alive rather than a static frozen shot,
  // without requiring the person to touch anything.
  useEffect(() => {
    const fg = fgRef.current;
    if (!fg) return;
    const timeout = setTimeout(() => {
      fg.zoomToFit(600, 80);
    }, 400);
    return () => clearTimeout(timeout);
  }, [graph]);

  const handleNodeClick = useCallback(
    (node: Node3D) => {
      onNodeSelect(node.nodeType, node.id);
      const fg = fgRef.current;
      if (fg && node.x !== undefined && node.y !== undefined && node.z !== undefined) {
        const distance = 120;
        const ratio = 1 + distance / Math.hypot(node.x, node.y, node.z || 1);
        fg.cameraPosition(
          { x: node.x * ratio, y: node.y * ratio, z: node.z * ratio },
          { x: node.x, y: node.y, z: node.z },
          800,
        );
      }
    },
    [onNodeSelect],
  );

  return (
    <ForceGraph3D<Node3D>
      ref={fgRef}
      graphData={graphData}
      backgroundColor="#0f1930"
      nodeLabel={(n: Node3D) => `${n.label} · ${formatNodeType(n.nodeType)}`}
      nodeThreeObject={(n) => createNodeObject(n.nodeType, n.id === rootId)}
      nodeThreeObjectExtend={false}
      linkColor={() => "rgba(255,255,255,0.18)"}
      linkWidth={0.4}
      linkDirectionalParticles={0}
      onNodeClick={handleNodeClick}
      showNavInfo={false}
      enableNodeDrag={true}
    />
  );
}
