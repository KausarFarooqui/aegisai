import type {
  AIOpportunityOut,
  AnalysisJobOut,
  AnalyzeProcessRequest,
  ApiError,
  DashboardOut,
  GraphNodeType,
  GraphResponse,
  ProcessDetailOut,
  ProcessSummaryOut,
  RoleOut,
  SkillOut,
  ValueChainOut,
} from "./types";

/**
 * Relative by design — works through Vite's dev proxy (see vite.config.ts)
 * and in production when the frontend is served behind the same origin as
 * the API (or a reverse proxy mapping /api). No hard-coded backend host
 * baked into the client.
 */
const BASE = "/api";

export class ApiRequestError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "ApiRequestError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });

  if (!res.ok) {
    let message = `Request failed (${res.status})`;
    try {
      const body: ApiError = await res.json();
      message = Array.isArray(body.detail)
        ? body.detail.map((d) => d.msg).join("; ")
        : body.detail ?? message;
    } catch {
      // response wasn't JSON — fall back to the generic message above
    }
    throw new ApiRequestError(res.status, message);
  }

  return res.json() as Promise<T>;
}

export const api = {
  getDashboard: () => request<DashboardOut>("/dashboard"),

  listProcesses: (limit = 100, offset = 0) =>
    request<ProcessSummaryOut[]>(`/processes?limit=${limit}&offset=${offset}`),

  getProcess: (id: string) => request<ProcessDetailOut>(`/processes/${id}`),

  listRoles: (limit = 100, offset = 0) =>
    request<RoleOut[]>(`/roles?limit=${limit}&offset=${offset}`),

  getRole: (id: string) => request<RoleOut>(`/roles/${id}`),

  listSkills: (opts?: { limit?: number; offset?: number; trend?: string }) => {
    const params = new URLSearchParams();
    if (opts?.limit) params.set("limit", String(opts.limit));
    if (opts?.offset) params.set("offset", String(opts.offset));
    if (opts?.trend) params.set("trend", opts.trend);
    return request<SkillOut[]>(`/skills?${params.toString()}`);
  },

  getSkill: (id: string) => request<SkillOut>(`/skills/${id}`),

  getGraph: (nodeType: GraphNodeType, nodeId: string, maxHops = 4) =>
    request<GraphResponse>(`/graph/${nodeType}/${nodeId}?max_hops=${maxHops}`),

  listOpportunities: (limit = 100, offset = 0) =>
    request<AIOpportunityOut[]>(`/opportunities?limit=${limit}&offset=${offset}`),

  listValueChains: () => request<ValueChainOut[]>("/value-chains"),

  analyzeProcess: (body: AnalyzeProcessRequest) =>
    request<AnalysisJobOut>("/processes/analyze", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  getAnalysisJob: (id: string) => request<AnalysisJobOut>(`/analysis/${id}`),
};
