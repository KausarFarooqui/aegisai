// Mirrors backend/app/schemas/*.py field-for-field. Kept snake_case to
// match the real JSON wire format exactly — no casing transform layer
// that could silently drift from the backend's actual response shape.

export type ImpactBand = "low" | "medium" | "high" | "very_high";

export type SkillTrend =
  | "emerging"
  | "increasing"
  | "ai_augmented"
  | "changing"
  | "declining"
  | "enduring_human_capability"
  | "unclassified";

export type AutomationPotential = "low" | "medium" | "high";

export type HumanAIResponsibility =
  | "ai_automates"
  | "ai_augments"
  | "human_led"
  | "human_approval_required";

export type EntitySource = "seed" | "dynamic";

export type AnalysisJobStatus = "pending" | "processing" | "completed" | "failed";

export type GraphNodeType = "process" | "activity" | "role" | "skill" | "ai_opportunity";

export interface SkillOut {
  id: string;
  name: string;
  category: string | null;
  trend_classification: SkillTrend;
  trend_rationale: string | null;
}

export interface RoleOut {
  id: string;
  title: string;
  current_responsibilities: string | null;
  skills: SkillOut[];
}

export interface AIAssessmentOut {
  factor_repetitiveness: number;
  factor_data_availability: number;
  factor_predictability: number;
  factor_digitalization: number;
  factor_ai_capability_fit: number;
  factor_rationale: Record<string, string>;
  total_score: number;
  impact_band: ImpactBand;
  scoring_model_version: string;
}

export interface AIOpportunityOut {
  id: string;
  name: string;
  description: string | null;
  automation_potential: AutomationPotential;
  human_ai_responsibility: HumanAIResponsibility;
  business_benefit: string | null;
  risks: string | null;
  source: EntitySource;
  assessment: AIAssessmentOut | null;
  affected_roles: RoleOut[];
  affected_skills: SkillOut[];
}

export interface ActivityOut {
  id: string;
  name: string;
  description: string | null;
  roles: RoleOut[];
  ai_opportunities: AIOpportunityOut[];
}

export interface ProcessSummaryOut {
  id: string;
  name: string;
  business_purpose: string | null;
  source: EntitySource;
  aggregate_ai_impact_score: number | null;
}

export interface ProcessDetailOut {
  id: string;
  name: string;
  business_purpose: string | null;
  current_challenges: string | null;
  source: EntitySource;
  activities: ActivityOut[];
}

export interface RoleImpactSummary {
  role_id: string;
  title: string;
  ai_opportunity_count: number;
}

export interface DashboardOut {
  total_processes: number;
  total_activities: number;
  total_roles: number;
  total_skills: number;
  total_ai_opportunities: number;
  high_impact_process_count: number;
  most_affected_roles: RoleImpactSummary[];
  emerging_skills: string[];
  declining_skills: string[];
}

export interface AnalyzeProcessRequest {
  process_name: string;
  value_chain_id: string;
  process_context?: string | null;
}

export interface AnalysisJobOut {
  id: string;
  target_type: string;
  input_name: string;
  input_context: string | null;
  status: AnalysisJobStatus;
  current_stage: string | null;
  model_used: string | null;
  started_at: string | null;
  completed_at: string | null;
  duration_ms: number | null;
  result_entity_id: string | null;
  error_message: string | null;
  stage_log: { stage: string; at: string }[];
}

export interface GraphNodeOut {
  id: string;
  type: GraphNodeType;
  label: string;
}

export interface GraphEdgeOut {
  source_id: string;
  source_type: GraphNodeType;
  target_id: string;
  target_type: GraphNodeType;
  label: string;
}

export interface GraphResponse {
  nodes: GraphNodeOut[];
  edges: GraphEdgeOut[];
}

export interface ValueChainOut {
  id: string;
  name: string;
  sequence_order: number;
}

export interface ApiError {
  detail: string | { msg: string; loc: (string | number)[] }[];
}
