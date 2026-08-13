import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/api/client";
import type { AnalyzeProcessRequest, GraphNodeType } from "@/api/types";

export function useDashboard() {
  return useQuery({ queryKey: ["dashboard"], queryFn: api.getDashboard });
}

export function useProcesses() {
  return useQuery({ queryKey: ["processes"], queryFn: () => api.listProcesses() });
}

export function useProcess(id: string | undefined) {
  return useQuery({
    queryKey: ["process", id],
    queryFn: () => api.getProcess(id!),
    enabled: !!id,
  });
}

export function useRoles() {
  return useQuery({ queryKey: ["roles"], queryFn: () => api.listRoles() });
}

export function useRole(id: string | undefined) {
  return useQuery({
    queryKey: ["role", id],
    queryFn: () => api.getRole(id!),
    enabled: !!id,
  });
}

export function useSkills(trend?: string) {
  return useQuery({
    queryKey: ["skills", trend],
    queryFn: () => api.listSkills(trend ? { trend } : undefined),
  });
}

export function useSkill(id: string | undefined) {
  return useQuery({
    queryKey: ["skill", id],
    queryFn: () => api.getSkill(id!),
    enabled: !!id,
  });
}

export function useGraph(nodeType: GraphNodeType | undefined, nodeId: string | undefined) {
  return useQuery({
    queryKey: ["graph", nodeType, nodeId],
    queryFn: () => api.getGraph(nodeType!, nodeId!),
    enabled: !!nodeType && !!nodeId,
  });
}

export function useOpportunities() {
  return useQuery({ queryKey: ["opportunities"], queryFn: () => api.listOpportunities() });
}

export function useValueChains() {
  return useQuery({ queryKey: ["valueChains"], queryFn: () => api.listValueChains() });
}

export function useAnalyzeProcess() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: AnalyzeProcessRequest) => api.analyzeProcess(body),
    onSuccess: () => {
      // A completed/failed analysis may have changed processes, roles,
      // skills, and dashboard counts — invalidate broadly rather than
      // track every possibly-affected query key individually.
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["processes"] });
      queryClient.invalidateQueries({ queryKey: ["roles"] });
      queryClient.invalidateQueries({ queryKey: ["skills"] });
    },
  });
}

/** Polls a job while it's pending/processing, stops once it reaches a
 * terminal state. Used for the (currently synchronous, but built to be
 * poll-friendly) analyze flow. */
export function useAnalysisJob(jobId: string | undefined) {
  return useQuery({
    queryKey: ["analysisJob", jobId],
    queryFn: () => api.getAnalysisJob(jobId!),
    enabled: !!jobId,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "pending" || status === "processing" ? 1000 : false;
    },
  });
}
