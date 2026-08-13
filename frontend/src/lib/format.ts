import type {
  AutomationPotential,
  EntitySource,
  GraphNodeType,
  HumanAIResponsibility,
  ImpactBand,
  SkillTrend,
} from "@/api/types";

const IMPACT_BAND_LABELS: Record<ImpactBand, string> = {
  low: "Low",
  medium: "Medium",
  high: "High",
  very_high: "Very High",
};
export function formatImpactBand(band: ImpactBand): string {
  return IMPACT_BAND_LABELS[band];
}

const TREND_LABELS: Record<SkillTrend, string> = {
  emerging: "Emerging",
  increasing: "Increasing",
  ai_augmented: "AI-Augmented",
  changing: "Changing",
  declining: "Declining",
  enduring_human_capability: "Enduring Human",
  unclassified: "Unclassified",
};
export function formatTrend(trend: SkillTrend): string {
  return TREND_LABELS[trend];
}

const RESPONSIBILITY_LABELS: Record<HumanAIResponsibility, string> = {
  ai_automates: "AI Automates",
  ai_augments: "AI Augments",
  human_led: "Human-Led",
  human_approval_required: "Human Approval Required",
};
export function formatResponsibility(r: HumanAIResponsibility): string {
  return RESPONSIBILITY_LABELS[r];
}

const AUTOMATION_POTENTIAL_LABELS: Record<AutomationPotential, string> = {
  low: "Low",
  medium: "Medium",
  high: "High",
};
export function formatAutomationPotential(p: AutomationPotential): string {
  return AUTOMATION_POTENTIAL_LABELS[p];
}

export function formatSource(s: EntitySource): string {
  return s === "seed" ? "Seed data" : "Dynamically analyzed";
}

const NODE_TYPE_LABELS: Record<GraphNodeType, string> = {
  process: "Process",
  activity: "Activity",
  role: "Role",
  skill: "Skill",
  ai_opportunity: "AI Opportunity",
};
export function formatNodeType(t: GraphNodeType): string {
  return NODE_TYPE_LABELS[t];
}

const STAGE_LABELS: Record<string, string> = {
  llm_extraction: "Extracting activities, roles, skills, and opportunities",
  dedup_matching: "Matching against existing roles and skills",
  scoring: "Computing deterministic AI impact scores",
  persistence: "Saving to the intelligence graph",
  evidence_retrieval: "Searching for supporting research",
  skill_trend_update: "Recomputing skill trends",
  graph_sync: "Updating graph relationships",
  done: "Complete",
};
export function formatStageLabel(stage: string): string {
  return STAGE_LABELS[stage] ?? stage;
}

export function formatDuration(ms: number | null): string {
  if (ms === null) return "—";
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

export function formatDateTime(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

export function truncate(text: string | null, max: number): string {
  if (!text) return "";
  return text.length > max ? `${text.slice(0, max).trimEnd()}…` : text;
}
