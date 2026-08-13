import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAnalyzeProcess, useValueChains } from "@/hooks/useApi";
import { PageHeader, StarMark } from "@/components/Layout";
import { Card, CardHeader } from "@/components/Card";
import { ErrorState } from "@/components/States";
import { formatDuration, formatStageLabel } from "@/lib/format";
import { Network, ArrowRight, CheckCircle2, XCircle } from "lucide-react";

const REFERENCE_STAGES = [
  "llm_extraction",
  "dedup_matching",
  "scoring",
  "persistence",
  "evidence_retrieval",
  "skill_trend_update",
  "graph_sync",
];

export function AnalyzePage() {
  const { data: valueChains, isLoading: loadingValueChains } = useValueChains();
  const { mutate, data: job, isPending, isError, error, reset } = useAnalyzeProcess();

  const [processName, setProcessName] = useState("");
  const [valueChainId, setValueChainId] = useState("");
  const [context, setContext] = useState("");
  const [elapsedMs, setElapsedMs] = useState(0);

  useEffect(() => {
    if (!isPending) return;
    const start = Date.now();
    const interval = setInterval(() => setElapsedMs(Date.now() - start), 100);
    return () => clearInterval(interval);
  }, [isPending]);

  const canSubmit = processName.trim().length >= 3 && valueChainId && !isPending;

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!canSubmit) return;
    mutate({
      process_name: processName.trim(),
      value_chain_id: valueChainId,
      process_context: context.trim() || undefined,
    });
  }

  function handleReset() {
    reset();
    setProcessName("");
    setContext("");
  }

  return (
    <>
      <PageHeader
        title="Analyze New Process"
        subtitle="Type in anything — a seeded process name or something the system has never seen. Same pipeline either way."
      />
      <div className="mx-auto max-w-2xl px-8 py-8">
        {!job && !isPending && (
          <Card>
            <form onSubmit={handleSubmit} className="space-y-5">
              <div>
                <label className="block text-sm font-medium text-[var(--color-ink)]">
                  Process name
                </label>
                <input
                  type="text"
                  value={processName}
                  onChange={(e) => setProcessName(e.target.value)}
                  placeholder="e.g. Warehouse Inventory Forecasting"
                  className="mt-1.5 w-full rounded-lg border border-[var(--color-border)] px-3 py-2.5 text-sm text-[var(--color-ink)] placeholder:text-slate-400 focus:border-[var(--color-star)] focus:outline-none"
                />
                <p className="mt-1 text-xs text-slate-400">At least 3 characters.</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-[var(--color-ink)]">
                  Value chain
                </label>
                <select
                  value={valueChainId}
                  onChange={(e) => setValueChainId(e.target.value)}
                  disabled={loadingValueChains}
                  className="mt-1.5 w-full rounded-lg border border-[var(--color-border)] bg-white px-3 py-2.5 text-sm text-[var(--color-ink)] focus:border-[var(--color-star)] focus:outline-none"
                >
                  <option value="">
                    {loadingValueChains ? "Loading…" : "Select a value chain"}
                  </option>
                  {valueChains?.map((vc) => (
                    <option key={vc.id} value={vc.id}>
                      {vc.name}
                    </option>
                  ))}
                </select>
                {valueChains?.length === 0 && (
                  <p className="mt-1 text-xs text-amber-600">
                    No value chains exist yet — run <code className="font-mono">scripts/bootstrap_minimal_data.py</code> first.
                  </p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-[var(--color-ink)]">
                  Additional context <span className="font-normal text-slate-400">(optional)</span>
                </label>
                <textarea
                  value={context}
                  onChange={(e) => setContext(e.target.value)}
                  rows={3}
                  placeholder="Anything that would help the analysis be more specific — otherwise the process name alone is enough."
                  className="mt-1.5 w-full resize-none rounded-lg border border-[var(--color-border)] px-3 py-2.5 text-sm text-[var(--color-ink)] placeholder:text-slate-400 focus:border-[var(--color-star)] focus:outline-none"
                />
              </div>

              {isError && <ErrorState message={(error as Error).message} />}

              <button
                type="submit"
                disabled={!canSubmit}
                className="flex w-full items-center justify-center gap-2 rounded-lg bg-[var(--color-navy)] px-4 py-3 text-sm font-medium text-white transition-colors hover:bg-[var(--color-navy-soft)] disabled:cursor-not-allowed disabled:opacity-40"
              >
                Run analysis
              </button>
            </form>
          </Card>
        )}

        {isPending && (
          <Card className="text-center">
            <div className="flex flex-col items-center py-6">
              <div className="relative">
                <div className="absolute inset-0 animate-ping rounded-full bg-[var(--color-star)]/30" />
                <div className="relative flex h-14 w-14 items-center justify-center rounded-full bg-[var(--color-navy-deep)]">
                  <StarMark className="h-6 w-6 animate-pulse" />
                </div>
              </div>
              <p className="mt-5 font-display font-medium text-[var(--color-ink)]">
                Analyzing "{processName}"
              </p>
              <p className="mt-1 font-mono text-xs tabular-nums text-slate-400">
                {(elapsedMs / 1000).toFixed(1)}s elapsed — typically 10–30s
              </p>
              <div className="mt-6 w-full space-y-1.5 text-left">
                {REFERENCE_STAGES.map((stage) => (
                  <div key={stage} className="flex items-center gap-2 text-xs text-slate-400">
                    <span className="h-1 w-1 rounded-full bg-slate-300" />
                    {formatStageLabel(stage)}
                  </div>
                ))}
              </div>
              <p className="mt-4 text-[11px] text-slate-400">
                This is one real call to Groq, running now — not a simulation.
              </p>
            </div>
          </Card>
        )}

        {job && job.status === "completed" && (
          <Card>
            <div className="flex items-center gap-2 text-[#3d8c5a]">
              <CheckCircle2 className="h-5 w-5" />
              <span className="font-display font-medium">Analysis complete</span>
            </div>
            <p className="mt-1 text-sm text-slate-500">
              "{job.input_name}" took {formatDuration(job.duration_ms)} across {job.stage_log.length}{" "}
              stages.
            </p>

            <div className="mt-5 flex gap-3">
              {job.result_entity_id && (
                <Link
                  to={`/processes/${job.result_entity_id}`}
                  className="flex flex-1 items-center justify-center gap-2 rounded-lg bg-[var(--color-navy)] px-4 py-2.5 text-sm font-medium text-white hover:bg-[var(--color-navy-soft)]"
                >
                  View process <ArrowRight className="h-4 w-4" />
                </Link>
              )}
              {job.result_entity_id && (
                <Link
                  to={`/graph?type=process&id=${job.result_entity_id}`}
                  className="flex items-center justify-center gap-2 rounded-lg border border-[var(--color-border)] px-4 py-2.5 text-sm font-medium text-[var(--color-ink)] hover:border-[var(--color-star)]/60"
                >
                  <Network className="h-4 w-4" /> View in graph
                </Link>
              )}
            </div>

            <div className="mt-6 border-t border-[var(--color-border)] pt-5">
              <CardHeader title="Pipeline stages" />
              <ol className="space-y-2">
                {job.stage_log.map((entry, i) => (
                  <li key={i} className="flex items-center justify-between text-sm">
                    <span className="text-slate-600">{formatStageLabel(entry.stage)}</span>
                    <span className="font-mono text-xs text-slate-400">
                      {new Date(entry.at).toLocaleTimeString()}
                    </span>
                  </li>
                ))}
              </ol>
            </div>

            <button
              onClick={handleReset}
              className="mt-6 text-sm font-medium text-[var(--color-navy)] hover:underline"
            >
              Analyze another process
            </button>
          </Card>
        )}

        {job && job.status === "failed" && (
          <Card>
            <div className="flex items-center gap-2 text-[#b4472a]">
              <XCircle className="h-5 w-5" />
              <span className="font-display font-medium">Analysis failed</span>
            </div>
            <p className="mt-2 text-sm text-slate-600">{job.error_message}</p>
            <p className="mt-3 text-xs text-slate-400">
              This is the pipeline catching and reporting a real problem — a validation check, or the
              LLM's response not matching the required shape — not a crash. Nothing was partially
              saved.
            </p>
            <button
              onClick={handleReset}
              className="mt-5 rounded-lg border border-[var(--color-border)] px-4 py-2 text-sm font-medium text-[var(--color-ink)] hover:border-[var(--color-star)]/60"
            >
              Try again
            </button>
          </Card>
        )}
      </div>
    </>
  );
}
