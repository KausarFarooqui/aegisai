import { Handle, Position } from "reactflow";
import type { GraphNodeType } from "@/api/types";
import { StarMark } from "./Layout";
import { cn } from "@/lib/cn";

const NODE_STYLE: Record<GraphNodeType, { dot: string; ring: string; text: string }> = {
  process: { dot: "bg-white", ring: "ring-2 ring-white", text: "text-white" },
  activity: { dot: "bg-slate-400", ring: "ring-1 ring-slate-500/40", text: "text-slate-300" },
  role: { dot: "bg-[#6f8fd6]", ring: "ring-1 ring-[#6f8fd6]/40", text: "text-[#a9bce8]" },
  skill: { dot: "bg-[#4fb3a9]", ring: "ring-1 ring-[#4fb3a9]/40", text: "text-[#8fd4cb]" },
  ai_opportunity: { dot: "", ring: "", text: "text-[var(--color-star-soft)]" },
};

export function ConstellationNode({
  data,
}: {
  data: { label: string; type: GraphNodeType; isFocused: boolean };
}) {
  const style = NODE_STYLE[data.type];
  const isOpportunity = data.type === "ai_opportunity";
  const isProcess = data.type === "process";

  return (
    <div className="group flex flex-col items-center gap-1.5" style={{ width: 140 }}>
      <Handle type="target" position={Position.Left} className="!opacity-0" />
      <Handle type="source" position={Position.Right} className="!opacity-0" />

      <div
        className={cn(
          "flex items-center justify-center rounded-full transition-transform group-hover:scale-125",
          isProcess ? "h-4 w-4" : "h-2.5 w-2.5",
          style.dot,
          style.ring,
          data.isFocused && "scale-150",
        )}
        style={
          isOpportunity
            ? {
                filter: "drop-shadow(0 0 6px var(--color-star))",
              }
            : undefined
        }
      >
        {isOpportunity && <StarMark className="h-4 w-4" />}
      </div>
      <span
        className={cn(
          "max-w-[140px] text-center text-[11px] leading-tight transition-opacity",
          style.text,
          "opacity-70 group-hover:opacity-100",
        )}
      >
        {data.label}
      </span>
    </div>
  );
}
