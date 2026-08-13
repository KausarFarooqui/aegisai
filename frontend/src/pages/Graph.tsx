import { useCallback, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import ReactFlow, {
  Background,
  BackgroundVariant,
  Controls,
  type Edge,
  type Node,
  type NodeMouseHandler,
} from "reactflow";
import "reactflow/dist/style.css";
import { useGraph, useProcesses } from "@/hooks/useApi";
import { PageHeader } from "@/components/Layout";
import { ConstellationNode } from "@/components/ConstellationNode";
import { LoadingState, EmptyState, ErrorState } from "@/components/States";
import { layoutGraph } from "@/lib/graphLayout";
import { formatNodeType } from "@/lib/format";
import type { GraphNodeType } from "@/api/types";

const nodeTypes = { constellation: ConstellationNode };

export function GraphPage() {
  const [params, setParams] = useSearchParams();
  const rootType = (params.get("type") as GraphNodeType | null) ?? undefined;
  const rootId = params.get("id") ?? undefined;

  const { data: processes } = useProcesses();
  const { data: graph, isLoading, isError, error, refetch } = useGraph(rootType, rootId);
  const [hoveredLabel, setHoveredLabel] = useState<string | null>(null);

  const selectNode = useCallback(
    (type: GraphNodeType, id: string) => {
      setParams({ type, id });
    },
    [setParams],
  );

  const { flowNodes, flowEdges } = useMemo(() => {
    if (!graph || !rootId) return { flowNodes: [] as Node[], flowEdges: [] as Edge[] };
    const positioned = layoutGraph(graph.nodes, graph.edges, rootId);

    const flowNodes: Node[] = positioned.map((n) => ({
      id: n.id,
      type: "constellation",
      position: { x: n.x, y: n.y },
      data: { label: n.label, type: n.type, isFocused: n.id === rootId },
      draggable: true,
    }));

    const flowEdges: Edge[] = graph.edges.map((e, i) => ({
      id: `${e.source_id}-${e.target_id}-${i}`,
      source: e.source_id,
      target: e.target_id,
      label: e.label,
      style: { stroke: "rgba(255,255,255,0.15)", strokeWidth: 1 },
      labelStyle: { fill: "rgba(255,255,255,0.35)", fontSize: 9 },
      labelBgStyle: { fill: "transparent" },
    }));

    return { flowNodes, flowEdges };
  }, [graph, rootId]);

  const handleNodeClick: NodeMouseHandler = useCallback(
    (_, node) => {
      const type = node.data.type as GraphNodeType;
      selectNode(type, node.id);
    },
    [selectNode],
  );

  return (
    <div className="flex h-screen flex-col">
      <PageHeader
        title="Intelligence Graph"
        subtitle="Every AI opportunity renders as a star — click any node to explore its neighborhood"
        action={
          <select
            className="rounded-lg border border-[var(--color-border)] bg-white px-3 py-2 text-sm text-[var(--color-ink)]"
            value={rootId ?? ""}
            onChange={(e) => {
              if (e.target.value) selectNode("process", e.target.value);
            }}
          >
            <option value="" disabled>
              Select a process to begin…
            </option>
            {processes?.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        }
      />

      <div className="relative flex-1 bg-[var(--color-navy-deep)]">
        {!rootId && (
          <div className="flex h-full items-center justify-center">
            <EmptyState
              title="Select a process to explore"
              description="Choose a process above — its full activity, role, skill, and AI opportunity neighborhood renders as a connected graph."
            />
          </div>
        )}
        {rootId && isLoading && (
          <div className="flex h-full items-center justify-center">
            <LoadingState label="Loading graph" />
          </div>
        )}
        {rootId && isError && (
          <div className="flex h-full items-center justify-center p-8">
            <ErrorState message={(error as Error).message} onRetry={() => refetch()} />
          </div>
        )}
        {rootId && graph && (
          <ReactFlow
            nodes={flowNodes}
            edges={flowEdges}
            nodeTypes={nodeTypes}
            onNodeClick={handleNodeClick}
            onNodeMouseEnter={(_, n) => setHoveredLabel(n.data.label)}
            onNodeMouseLeave={() => setHoveredLabel(null)}
            fitView
            fitViewOptions={{ padding: 0.3 }}
            proOptions={{ hideAttribution: true }}
            minZoom={0.3}
          >
            <Background variant={BackgroundVariant.Dots} color="rgba(255,255,255,0.06)" gap={24} />
            <Controls className="!bg-white/5 [&>button]:!border-white/10 [&>button]:!bg-white/5 [&>button]:!fill-white [&>button:hover]:!bg-white/15" />
          </ReactFlow>
        )}

        {hoveredLabel && (
          <div className="pointer-events-none absolute bottom-6 left-1/2 -translate-x-1/2 rounded-full bg-black/60 px-4 py-1.5 text-xs text-white backdrop-blur-sm">
            {hoveredLabel}
          </div>
        )}

        {graph && (
          <div className="absolute right-4 top-4 rounded-lg bg-black/40 px-3 py-2 text-[11px] text-white/60 backdrop-blur-sm">
            <Legend />
          </div>
        )}
      </div>
    </div>
  );
}

function Legend() {
  const items: { type: GraphNodeType; color: string }[] = [
    { type: "process", color: "bg-white" },
    { type: "activity", color: "bg-slate-400" },
    { type: "role", color: "bg-[#6f8fd6]" },
    { type: "skill", color: "bg-[#4fb3a9]" },
    { type: "ai_opportunity", color: "bg-[var(--color-star)]" },
  ];
  return (
    <div className="space-y-1">
      {items.map((item) => (
        <div key={item.type} className="flex items-center gap-2">
          <span className={`h-2 w-2 rounded-full ${item.color}`} />
          {formatNodeType(item.type)}
        </div>
      ))}
    </div>
  );
}
